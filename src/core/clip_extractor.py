"""
Clip Extractor - Extract video clips using FFmpeg based on segments
"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ClipExtractor:
    """Extract video clips using FFmpeg"""
    
    def __init__(self, config):
        """
        Initialize clip extractor
        
        Args:
            config: Video processing configuration dictionary
        """
        self.config = config
        self.min_duration = config.get('min_clip_duration', 15)
        self.max_duration = config.get('max_clip_duration', 60)
        self.quality_crf = config.get('quality_crf', 23)
        self.audio_bitrate = config.get('audio_bitrate', '128k')
        self.video_codec = config.get('video_codec', 'libx264')
        self.audio_codec = config.get('audio_codec', 'aac')
    
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
    
    def _build_ffmpeg_command(self, input_path, output_path, start_time, duration, filters=None):
        """
        Build FFmpeg command
        
        Args:
            input_path: Input video path
            output_path: Output video path
            start_time: Start time in seconds
            duration: Duration in seconds
            filters: Optional video filters
            
        Returns:
            List of command arguments
        """
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', self.video_codec,
            '-crf', str(self.quality_crf),
            '-c:a', self.audio_codec,
            '-b:a', self.audio_bitrate,
        ]
        
        # Add video filters if specified
        if filters:
            cmd.extend(['-vf', filters])
        
        # Output file (overwrite if exists)
        cmd.extend(['-y', output_path])
        
        return cmd
    
    def extract_clip(self, video_path, segment, output_dir, filename_prefix="clip"):
        """
        Extract a single clip from video
        
        Args:
            video_path: Source video path
            segment: Segment dictionary with start_time and end_time
            output_dir: Output directory
            filename_prefix: Prefix for output filename
            
        Returns:
            Path to extracted clip or None if failed
        """
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg is required but not found")
        
        # Calculate duration
        start_time = segment.get('start_time', 0)
        end_time = segment.get('end_time', 0)
        duration = end_time - start_time
        
        # Validate duration
        if duration < self.min_duration:
            logger.warning(f"Segment duration {duration}s is below minimum {self.min_duration}s")
            return None
        
        if duration > self.max_duration:
            logger.warning(f"Segment duration {duration}s exceeds maximum {self.max_duration}s, trimming")
            duration = self.max_duration
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        video_name = Path(video_path).stem
        output_filename = f"{filename_prefix}_{video_name}_{int(start_time)}_{int(end_time)}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(
            video_path,
            output_path,
            start_time,
            duration
        )
        
        logger.info(f"Extracting clip: {start_time}s to {end_time}s from {video_path}")
        
        try:
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Verify output file exists
            if os.path.exists(output_path):
                logger.info(f"Clip extracted successfully: {output_path}")
                return output_path
            else:
                logger.error("FFmpeg completed but output file not found")
                return None
        
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Clip extraction failed: {e}")
            return None
    
    def extract_clips(self, video_path, segments, output_dir):
        """
        Extract multiple clips from video
        
        Args:
            video_path: Source video path
            segments: List of segment dictionaries
            output_dir: Output directory
            
        Returns:
            List of extracted clip paths
        """
        clips = []
        
        for i, segment in enumerate(segments):
            clip_path = self.extract_clip(
                video_path,
                segment,
                output_dir,
                filename_prefix=f"clip_{i+1:02d}"
            )
            
            if clip_path:
                clips.append({
                    'path': clip_path,
                    'segment': segment
                })
        
        logger.info(f"Extracted {len(clips)} clips from {video_path}")
        return clips
    
    def apply_filters(self, video_path, output_path, filters):
        """
        Apply video filters to a clip
        
        Args:
            video_path: Input video path
            output_path: Output video path
            filters: FFmpeg filter string
            
        Returns:
            True if successful, False otherwise
        """
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg is required but not found")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filters,
            '-c:v', self.video_codec,
            '-crf', str(self.quality_crf),
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y', output_path
        ]
        
        logger.info(f"Applying filters to {video_path}")
        
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"Filters applied successfully: {output_path}")
                return True
            else:
                logger.error("FFmpeg completed but output file not found")
                return False
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Filter application failed: {e.stderr.decode()}")
            return False
    
    def get_video_info(self, video_path):
        """
        Get video information using FFprobe
        
        Args:
            video_path: Video file path
            
        Returns:
            Dictionary with video information
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            import json
            info = json.loads(result.stdout.decode())
            
            # Extract useful information
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            
            if video_stream:
                return {
                    'duration': float(info['format'].get('duration', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'codec': video_stream.get('codec_name', ''),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1'))
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}
