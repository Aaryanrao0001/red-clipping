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
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
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
        
        # Check cache first
        cache_path = self._get_cache_path(video_path, 'video_analysis')
        cached_result = self._load_from_cache(cache_path)
        if cached_result:
            return cached_result
        
        # Get analysis prompt
        analysis_prompt = self.prompts.get('video_analysis_prompt', '')
        
        # Add video metadata to prompt if available
        prompt = analysis_prompt
        if video_metadata:
            prompt += f"\n\nVideo Metadata:\n{json.dumps(video_metadata, indent=2)}"
        else:
            prompt += f"\n\nVideo File: {os.path.basename(video_path)}"
        
        # Note: In a real implementation, you would extract frames/audio from the video
        # and send them to the API. For now, we'll work with metadata only.
        prompt += "\n\nNote: Analyze based on the video file name and any provided metadata. In production, actual video frames and audio would be analyzed."
        
        try:
            # Call API
            response_text = self._call_api(prompt)
            
            # Parse JSON response
            # Try to extract JSON from the response
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            
            # Validate result structure
            if 'segments' not in result:
                logger.warning("API response missing 'segments' key")
                result = {'segments': [], 'overall_assessment': response_text}
            
            # Save to cache
            self._save_to_cache(cache_path, result)
            
            logger.info(f"Analysis complete: found {len(result.get('segments', []))} segments")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {e}")
            # Return a basic structure
            return {
                'segments': [],
                'overall_assessment': 'Analysis failed: Invalid JSON response',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise
    
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
