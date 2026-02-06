"""
Format Optimizer - Optimize video format for different platforms
"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FormatOptimizer:
    """Optimize video format for platform-specific requirements"""
    
    def __init__(self, config, platform_settings):
        """
        Initialize format optimizer
        
        Args:
            config: Video configuration dictionary
            platform_settings: Platform-specific settings
        """
        self.config = config
        self.platform_settings = platform_settings
        self.target_aspect_ratio = config.get('target_aspect_ratio', '9:16')
        self.video_codec = config.get('video_codec', 'libx264')
        self.audio_codec = config.get('audio_codec', 'aac')
        self.quality_crf = config.get('quality_crf', 23)
    
    def _parse_aspect_ratio(self, aspect_ratio):
        """Parse aspect ratio string to width:height ratio"""
        parts = aspect_ratio.split(':')
        if len(parts) == 2:
            return int(parts[0]) / int(parts[1])
        return None
    
    def _calculate_dimensions(self, current_width, current_height, target_aspect):
        """
        Calculate new dimensions to match target aspect ratio
        
        Args:
            current_width: Current video width
            current_height: Current video height
            target_aspect: Target aspect ratio (e.g., "9:16")
            
        Returns:
            Tuple of (width, height, crop_params)
        """
        target_ratio = self._parse_aspect_ratio(target_aspect)
        if not target_ratio:
            return current_width, current_height, None
        
        current_ratio = current_width / current_height
        
        # For 9:16 (vertical), target ratio is 0.5625
        if abs(current_ratio - target_ratio) < 0.01:
            # Already correct aspect ratio
            return current_width, current_height, None
        
        # Calculate dimensions for target aspect ratio
        if current_ratio > target_ratio:
            # Video is too wide, crop width
            new_width = int(current_height * target_ratio)
            new_height = current_height
            crop_x = (current_width - new_width) // 2
            crop_y = 0
        else:
            # Video is too tall, crop height
            new_width = current_width
            new_height = int(current_width / target_ratio)
            crop_x = 0
            crop_y = (current_height - new_height) // 2
        
        # Ensure even dimensions (required for many codecs)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        
        crop_params = f"{new_width}:{new_height}:{crop_x}:{crop_y}"
        
        return new_width, new_height, crop_params
    
    def optimize_for_platform(self, video_path, platform, output_dir=None):
        """
        Optimize video for specific platform
        
        Args:
            video_path: Input video path
            platform: Platform name (instagram, youtube, tiktok)
            output_dir: Optional output directory
            
        Returns:
            Path to optimized video or None if failed
        """
        if platform not in self.platform_settings:
            logger.error(f"Unknown platform: {platform}")
            return None
        
        platform_config = self.platform_settings[platform]
        
        # Get video info
        from .clip_extractor import ClipExtractor
        extractor = ClipExtractor(self.config)
        video_info = extractor.get_video_info(video_path)
        
        if not video_info:
            logger.error(f"Failed to get video info for {video_path}")
            return None
        
        # Check platform requirements
        max_duration = platform_config.get('max_duration', 60)
        target_aspect = platform_config.get('aspect_ratio', self.target_aspect_ratio)
        max_file_size_mb = platform_config.get('max_file_size_mb', 100)
        
        current_width = video_info.get('width', 0)
        current_height = video_info.get('height', 0)
        current_duration = video_info.get('duration', 0)
        
        # Calculate target dimensions
        new_width, new_height, crop_params = self._calculate_dimensions(
            current_width, current_height, target_aspect
        )
        
        # Setup output path
        if output_dir is None:
            output_dir = os.path.dirname(video_path)
        
        os.makedirs(output_dir, exist_ok=True)
        
        video_name = Path(video_path).stem
        output_filename = f"{video_name}_{platform}_optimized.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-i', video_path]
        
        # Add filters
        filters = []
        
        # Crop to target aspect ratio if needed
        if crop_params:
            filters.append(f"crop={crop_params}")
        
        # Scale to standard resolution (1080x1920 for 9:16)
        if target_aspect == "9:16":
            target_width = 1080
            target_height = 1920
            filters.append(f"scale={target_width}:{target_height}")
        
        # Apply filters
        if filters:
            cmd.extend(['-vf', ','.join(filters)])
        
        # Codec settings
        cmd.extend([
            '-c:v', self.video_codec,
            '-crf', str(self.quality_crf),
            '-preset', 'medium',
            '-c:a', self.audio_codec,
            '-b:a', '128k',
            '-movflags', '+faststart',  # Enable progressive download
        ])
        
        # Limit duration if needed
        if current_duration > max_duration:
            cmd.extend(['-t', str(max_duration)])
        
        # Output file
        cmd.extend(['-y', output_path])
        
        logger.info(f"Optimizing video for {platform}: {video_path}")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            if os.path.exists(output_path):
                # Check file size
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                
                if file_size_mb > max_file_size_mb:
                    logger.warning(f"Output file size ({file_size_mb:.2f}MB) exceeds limit ({max_file_size_mb}MB)")
                    # Could implement re-encoding with lower quality here
                
                logger.info(f"Video optimized for {platform}: {output_path} ({file_size_mb:.2f}MB)")
                return output_path
            else:
                logger.error("Optimization completed but output file not found")
                return None
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Video optimization failed: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return None
    
    def batch_optimize(self, video_paths, platforms, output_dir):
        """
        Optimize multiple videos for multiple platforms
        
        Args:
            video_paths: List of video paths
            platforms: List of platform names
            output_dir: Output directory
            
        Returns:
            Dictionary mapping video paths to platform-optimized paths
        """
        results = {}
        
        for video_path in video_paths:
            results[video_path] = {}
            
            for platform in platforms:
                optimized_path = self.optimize_for_platform(
                    video_path,
                    platform,
                    output_dir
                )
                
                if optimized_path:
                    results[video_path][platform] = optimized_path
        
        return results
    
    def add_watermark(self, video_path, watermark_path, output_path, position="bottom_right"):
        """
        Add watermark to video
        
        Args:
            video_path: Input video path
            watermark_path: Watermark image path
            output_path: Output video path
            position: Watermark position (top_left, top_right, bottom_left, bottom_right)
            
        Returns:
            True if successful, False otherwise
        """
        # Position mappings
        positions = {
            'top_left': '10:10',
            'top_right': 'W-w-10:10',
            'bottom_left': '10:H-h-10',
            'bottom_right': 'W-w-10:H-h-10'
        }
        
        overlay_pos = positions.get(position, positions['bottom_right'])
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', watermark_path,
            '-filter_complex', f"overlay={overlay_pos}",
            '-codec:a', 'copy',
            '-y', output_path
        ]
        
        logger.info(f"Adding watermark to {video_path}")
        
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"Watermark added: {output_path}")
                return True
            
            return False
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Watermark addition failed: {e.stderr.decode()}")
            return False
