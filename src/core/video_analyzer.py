"""
Video Analyzer - AI-powered video content analysis using GitHub Models API
"""
import os
import json
import logging
import hashlib
import requests
from datetime import datetime, timedelta
import yaml
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Analyze videos using AI to identify viral-worthy segments"""
    
    def __init__(self, config, prompts_config, credential_manager):
        """
        Initialize video analyzer
        
        Args:
            config: AI configuration dictionary
            prompts_config: AI prompts configuration
            credential_manager: CredentialManager instance
        """
        self.config = config
        self.prompts = prompts_config
        self.credential_manager = credential_manager
        self.api_endpoint = config.get('api_endpoint')
        self.model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 4000)
        self.enable_cache = config.get('enable_cache', True)
        self.cache_dir = config.get('cache_dir', 'cache/ai_responses')
        self.cache_expiration_hours = config.get('cache_expiration_hours', 24)
        
        # Whisper model configuration
        self.whisper_model_size = config.get('whisper_model_size', 'base')
        self.whisper_model = None  # Lazy load Whisper model
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_api_token(self):
        """Get GitHub API token from credential manager or environment"""
        token = self.credential_manager.decrypt_credential('github_api', 'token')
        if not token:
            token = os.getenv('GITHUB_TOKEN')
        return token
    
    def _get_cache_path(self, video_path, prompt_type):
        """Generate cache file path for video and prompt type"""
        # Create hash of video path and prompt type
        cache_key = hashlib.md5(f"{video_path}_{prompt_type}".encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _load_from_cache(self, cache_path):
        """Load analysis from cache if valid"""
        if not self.enable_cache or not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached.get('timestamp'))
            expiration = timedelta(hours=self.cache_expiration_hours)
            
            if datetime.now() - cached_time < expiration:
                logger.info(f"Loaded analysis from cache: {cache_path}")
                return cached.get('data')
        
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_path, data):
        """Save analysis to cache"""
        if not self.enable_cache:
            return
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Saved analysis to cache: {cache_path}")
        
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _call_api(self, prompt, system_prompt=None):
        """
        Call GitHub Models API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            API response text
        """
        token = self._get_api_token()
        if not token:
            raise ValueError("GitHub API token not found. Set GITHUB_TOKEN environment variable or configure credentials.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Log status code for debugging
            logger.debug(f"API response status code: {response.status_code}")
            
            # Check if response is successful
            if response.status_code != 200:
                logger.error(f"API returned non-200 status code: {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")  # Log first 500 chars
                response.raise_for_status()
            
            # Check if response has content
            if not response.text or response.text.strip() == '':
                logger.error("API returned empty response")
                raise ValueError("Empty response from API")
            
            # Log raw response for debugging (first 200 chars)
            logger.debug(f"Raw API response (first 200 chars): {response.text[:200]}")
            
            # Parse JSON response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response as JSON: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                raise ValueError(f"Invalid JSON response from API: {e}")
            
            # Extract content from response
            if 'choices' not in result or len(result['choices']) == 0:
                logger.error(f"API response missing 'choices' key or empty choices")
                logger.error(f"Response structure: {json.dumps(result, indent=2)[:500]}")
                raise ValueError("Invalid API response structure")
            
            content = result['choices'][0]['message']['content']
            
            # Validate content is not empty
            if not content or content.strip() == '':
                logger.error("API returned empty content in message")
                raise ValueError("Empty content from API")
            
            return content
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
            raise
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
    
    def _extract_audio(self, video_path, output_audio_path=None):
        """
        Extract audio from video using FFmpeg
        
        Args:
            video_path: Path to video file
            output_audio_path: Optional path for output audio file
            
        Returns:
            Path to extracted audio file or None if failed
        """
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg is required but not found")
        
        # Create output path if not provided
        if output_audio_path is None:
            # Create temp file in cache directory
            temp_dir = os.path.join(self.cache_dir, 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
            
            video_name = Path(video_path).stem
            output_audio_path = os.path.join(temp_dir, f"{video_name}_audio.wav")
        
        logger.info(f"Extracting audio from video: {video_path}")
        
        # FFmpeg command to extract audio
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM format for Whisper
            '-ar', '16000',  # 16kHz sample rate (Whisper's native rate)
            '-ac', '1',  # Mono audio
            '-y',  # Overwrite output file
            output_audio_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 0:
                logger.info(f"Audio extracted successfully: {output_audio_path}")
                return output_audio_path
            else:
                logger.error("FFmpeg completed but audio file not found or empty")
                return None
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None
    
    def _load_whisper_model(self):
        """Load Whisper model (lazy loading)"""
        if self.whisper_model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.whisper_model_size}")
                self.whisper_model = whisper.load_model(self.whisper_model_size)
                logger.info("Whisper model loaded successfully")
            except ImportError:
                raise ImportError(
                    "Whisper is not installed. Install it with: pip install openai-whisper"
                )
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        
        return self.whisper_model
    
    def _transcribe_audio(self, audio_path):
        """
        Transcribe audio using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription results or None if failed
        """
        if not audio_path or not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
        
        try:
            # Load Whisper model
            model = self._load_whisper_model()
            
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe audio
            result = model.transcribe(audio_path)
            
            # Validate result
            if not result or 'text' not in result:
                logger.error("Whisper transcription returned invalid result")
                return None
            
            transcript_text = result['text'].strip()
            
            if not transcript_text:
                logger.warning("Whisper transcription returned empty text")
                return None
            
            logger.info(f"Transcription completed. Length: {len(transcript_text)} characters")
            logger.debug(f"Transcript preview: {transcript_text[:200]}...")
            
            return result
        
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}", exc_info=True)
            return None
    
    def _extract_frames(self, video_path, interval_seconds=2, max_frames=10):
        """
        Extract frames from video at regular intervals
        
        Args:
            video_path: Path to video file
            interval_seconds: Extract frame every N seconds
            max_frames: Maximum number of frames to extract
            
        Returns:
            List of frame file paths or empty list if failed
        """
        if not self._check_ffmpeg():
            logger.warning("FFmpeg not available, skipping frame extraction")
            return []
        
        # Create temp directory for frames
        temp_dir = os.path.join(self.cache_dir, 'temp_frames')
        os.makedirs(temp_dir, exist_ok=True)
        
        video_name = Path(video_path).stem
        frame_pattern = os.path.join(temp_dir, f"{video_name}_frame_%03d.jpg")
        
        logger.info(f"Extracting frames from video: {video_path}")
        
        # FFmpeg command to extract frames
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps=1/{interval_seconds}',  # Extract 1 frame every N seconds
            '-frames:v', str(max_frames),  # Limit number of frames
            '-y',
            frame_pattern
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Find extracted frames
            frames = sorted([
                os.path.join(temp_dir, f) 
                for f in os.listdir(temp_dir) 
                if f.startswith(f"{video_name}_frame_") and f.endswith('.jpg')
            ])
            
            if frames:
                logger.info(f"Extracted {len(frames)} frames")
                return frames
            else:
                logger.warning("No frames extracted")
                return []
        
        except subprocess.CalledProcessError as e:
            logger.warning(f"Frame extraction failed: {e.stderr.decode()}")
            return []
        except Exception as e:
            logger.warning(f"Frame extraction failed: {e}")
            return []
    
    def analyze_video(self, video_path, video_metadata=None):
        """
        Analyze video to identify viral-worthy segments
        
        Args:
            video_path: Path to video file
            video_metadata: Optional metadata about the video
            
        Returns:
            Dictionary containing analysis results with segments
        """
        logger.info(f"Analyzing video: {video_path}")
        
        # Validate video file exists
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {
                'segments': [],
                'overall_assessment': 'Analysis failed: Video file not found',
                'error': 'File not found'
            }
        
        # Check cache first
        cache_path = self._get_cache_path(video_path, 'video_analysis')
        cached_result = self._load_from_cache(cache_path)
        if cached_result:
            return cached_result
        
        try:
            # Step 1: Extract audio from video
            logger.info("Step 1/4: Extracting audio from video...")
            audio_path = self._extract_audio(video_path)
            
            if not audio_path:
                logger.error("Failed to extract audio from video")
                return {
                    'segments': [],
                    'overall_assessment': 'Analysis failed: Could not extract audio from video',
                    'error': 'Audio extraction failed'
                }
            
            # Step 2: Transcribe audio using Whisper
            logger.info("Step 2/4: Transcribing audio with Whisper...")
            transcription_result = self._transcribe_audio(audio_path)
            
            # Clean up audio file
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.debug(f"Cleaned up temporary audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up audio file: {e}")
            
            if not transcription_result:
                logger.error("Failed to transcribe audio")
                return {
                    'segments': [],
                    'overall_assessment': 'Analysis failed: Could not transcribe audio',
                    'error': 'Transcription failed'
                }
            
            transcript_text = transcription_result.get('text', '').strip()
            
            if not transcript_text:
                logger.error("Transcription returned empty text")
                return {
                    'segments': [],
                    'overall_assessment': 'Analysis failed: Empty transcription',
                    'error': 'Empty transcript'
                }
            
            logger.info(f"Transcription successful: {len(transcript_text)} characters")
            
            # Step 3: Extract frames (optional, for future vision analysis)
            logger.info("Step 3/4: Extracting key frames from video...")
            frames = self._extract_frames(video_path, interval_seconds=2, max_frames=10)
            
            # Clean up frames (we're not using them yet, but they're available for future vision models)
            for frame_path in frames:
                try:
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                        logger.debug(f"Cleaned up frame: {frame_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up frame: {e}")
            
            # Step 4: Construct prompt with transcript
            logger.info("Step 4/4: Analyzing transcript with AI...")
            
            # Get analysis prompt
            analysis_prompt = self.prompts.get('video_analysis_prompt', '')
            
            # Build comprehensive prompt with transcript
            prompt = analysis_prompt
            prompt += f"\n\n## Video Transcript\n\nThe following is the complete transcript of the video:\n\n\"\"\"\n{transcript_text}\n\"\"\"\n"
            
            # Add video metadata if available
            if video_metadata:
                prompt += f"\n\n## Video Metadata\n{json.dumps(video_metadata, indent=2)}"
            else:
                prompt += f"\n\n## Video File\n{os.path.basename(video_path)}"
            
            # Add frame info if available
            if frames:
                prompt += f"\n\n## Visual Information\nExtracted {len(frames)} key frames from the video at 2-second intervals."
            
            # Add instruction to analyze based on transcript
            prompt += "\n\n## Instructions\nAnalyze the transcript above to identify viral-worthy segments. Focus on the spoken content, narrative flow, and emotional moments captured in the text. Identify segments that would work well as 15-60 second clips for social media."
            
            # Validate prompt is not empty
            if not prompt or len(prompt.strip()) < 100:
                logger.error("Generated prompt is too short or empty")
                return {
                    'segments': [],
                    'overall_assessment': 'Analysis failed: Invalid prompt generated',
                    'error': 'Invalid prompt'
                }
            
            # Call API with the transcript-based prompt
            response_text = self._call_api(prompt)
            
            # Parse JSON response
            # Try to extract JSON from the response
            response_text = response_text.strip()
            
            # Log raw response for debugging (first 300 chars)
            logger.debug(f"Raw response text (first 300 chars): {response_text[:300]}")
            
            # Remove markdown code blocks if present
            # Handle both ```json and ``` formats
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Remove first line (``` or ```json)
                lines = lines[1:]
                # Remove last line if it's just ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response_text = '\n'.join(lines).strip()
                logger.debug("Stripped markdown code blocks from response")
            
            # Try to parse JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response as JSON: {e}")
                logger.error(f"Response text after processing: {response_text[:500]}")
                # Return a basic structure with error info
                return {
                    'segments': [],
                    'overall_assessment': 'Analysis failed: Invalid JSON response from API',
                    'error': str(e),
                    'raw_response': response_text[:500]  # Include first 500 chars for debugging
                }
            
            # Validate result structure
            if 'segments' not in result:
                logger.warning("API response missing 'segments' key")
                result = {'segments': [], 'overall_assessment': response_text}
            
            # Add transcript to result for reference
            result['transcript'] = transcript_text
            
            # Save to cache
            self._save_to_cache(cache_path, result)
            
            logger.info(f"Analysis complete: found {len(result.get('segments', []))} segments")
            return result
        
        except Exception as e:
            logger.error(f"Video analysis failed: {e}", exc_info=True)
            return {
                'segments': [],
                'overall_assessment': f'Analysis failed: {str(e)}',
                'error': str(e)
            }
    
    def filter_segments(self, segments, min_score=70):
        """
        Filter segments by viral score
        
        Args:
            segments: List of segment dictionaries
            min_score: Minimum viral score threshold
            
        Returns:
            Filtered list of segments
        """
        filtered = [s for s in segments if s.get('viral_score', 0) >= min_score]
        logger.info(f"Filtered {len(segments)} segments to {len(filtered)} (min_score={min_score})")
        return filtered
    
    def rank_segments(self, segments):
        """
        Rank segments by viral score
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Sorted list of segments (highest score first)
        """
        ranked = sorted(segments, key=lambda x: x.get('viral_score', 0), reverse=True)
        return ranked
    
    def get_best_segments(self, video_path, min_score=70, max_segments=5):
        """
        Analyze video and return best segments
        
        Args:
            video_path: Path to video file
            min_score: Minimum viral score
            max_segments: Maximum number of segments to return
            
        Returns:
            List of top segments
        """
        # Analyze video
        analysis = self.analyze_video(video_path)
        
        # Get segments
        segments = analysis.get('segments', [])
        
        # Filter and rank
        filtered = self.filter_segments(segments, min_score)
        ranked = self.rank_segments(filtered)
        
        # Return top segments
        return ranked[:max_segments]
