"""
Main orchestrator for autonomous video clipping and publishing system
"""
import os
import sys
import argparse
import logging
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.credential_manager import CredentialManager
from utils.state_manager import StateManager
from utils.browser_manager import BrowserManager
from core.video_analyzer import VideoAnalyzer
from core.clip_extractor import ClipExtractor
from core.format_optimizer import FormatOptimizer
from core.metadata_generator import MetadataGenerator
from upload.instagram_uploader import InstagramUploader
from upload.youtube_uploader import YouTubeUploader
from upload.tiktok_uploader import TikTokUploader
from upload.upload_scheduler import UploadScheduler


def setup_logging(config):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Setup handlers
    handlers = []
    
    if log_config.get('console_logging', True):
        handlers.append(logging.StreamHandler())
    
    if log_config.get('file_logging', True):
        log_dir = config.get('paths', {}).get('output_logs', 'output/logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'app.log')
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )


def load_config():
    """Load configuration files"""
    with open('config/settings.yaml', 'r') as f:
        settings = yaml.safe_load(f)
    
    with open('config/ai_prompts.yaml', 'r') as f:
        prompts = yaml.safe_load(f)
    
    return settings, prompts


class VideoClippingSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        """Initialize the system"""
        # Load configurations
        self.settings, self.prompts = load_config()
        
        # Setup logging
        setup_logging(self.settings)
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.credential_manager = CredentialManager()
        self.state_manager = StateManager(self.settings['paths']['state_files'])
        self.browser_manager = BrowserManager(self.settings['browser'])
        
        # Initialize AI configuration with cache directory
        ai_config = self.settings['ai'].copy()
        ai_config['cache_dir'] = self.settings['paths']['cache_ai']
        
        # Initialize core components
        self.video_analyzer = VideoAnalyzer(
            ai_config, 
            self.prompts, 
            self.credential_manager
        )
        self.clip_extractor = ClipExtractor(self.settings['video'])
        self.format_optimizer = FormatOptimizer(
            self.settings['video'], 
            self.settings['platforms']
        )
        self.metadata_generator = MetadataGenerator(
            self.settings['metadata'], 
            self.prompts, 
            self.video_analyzer
        )
        
        # Initialize upload components
        self.instagram_uploader = InstagramUploader(
            self.browser_manager, 
            self.credential_manager
        )
        self.youtube_uploader = YouTubeUploader(
            self.browser_manager, 
            self.credential_manager
        )
        self.tiktok_uploader = TikTokUploader(
            self.browser_manager, 
            self.credential_manager
        )
        
        # Initialize scheduler
        self.upload_scheduler = UploadScheduler(
            self.settings['scheduling'], 
            self.state_manager
        )
        
        self.logger.info("Video Clipping System initialized")
    
    def discover_videos(self):
        """Discover video files in input directory"""
        input_dir = self.settings['paths']['input_videos']
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        
        videos = []
        for ext in video_extensions:
            videos.extend(Path(input_dir).glob(f'*{ext}'))
        
        self.logger.info(f"Discovered {len(videos)} videos in {input_dir}")
        return [str(v) for v in videos]
    
    def process_video(self, video_path, platforms=None, auto_upload=False):
        """
        Process a single video: analyze, extract clips, optimize, and schedule uploads
        
        Args:
            video_path: Path to video file
            platforms: List of platforms to upload to (default: all)
            auto_upload: Whether to automatically schedule uploads
            
        Returns:
            Dictionary with processing results
        """
        if platforms is None:
            platforms = ['instagram', 'youtube', 'tiktok']
        
        self.logger.info(f"Processing video: {video_path}")
        
        results = {
            'video_path': video_path,
            'clips': [],
            'scheduled_uploads': []
        }
        
        try:
            # Step 1: Analyze video
            self.logger.info("Step 1: Analyzing video...")
            segments = self.video_analyzer.get_best_segments(
                video_path,
                min_score=70,
                max_segments=5
            )
            
            if not segments:
                self.logger.warning("No viral segments found in video")
                return results
            
            self.logger.info(f"Found {len(segments)} viral segments")
            
            # Step 2: Extract clips
            self.logger.info("Step 2: Extracting clips...")
            output_dir = self.settings['paths']['output_clips']
            clips = self.clip_extractor.extract_clips(video_path, segments, output_dir)
            
            if not clips:
                self.logger.warning("No clips extracted")
                return results
            
            results['clips'] = clips
            
            # Step 3: Optimize and generate metadata for each platform
            self.logger.info("Step 3: Optimizing clips and generating metadata...")
            for clip_info in clips:
                clip_path = clip_info['path']
                
                # Generate metadata for all platforms
                metadata = self.metadata_generator.generate_metadata_for_clip(
                    clip_info, 
                    platforms
                )
                
                # Optimize for each platform
                for platform in platforms:
                    optimized_path = self.format_optimizer.optimize_for_platform(
                        clip_path, 
                        platform
                    )
                    
                    if optimized_path and auto_upload:
                        # Create upload task
                        upload_task = {
                            'video_path': video_path,
                            'clip_path': optimized_path,
                            'platform': platform,
                            'metadata': metadata.get(platform, {})
                        }
                        
                        # Schedule upload
                        upload_function = self._get_upload_function(platform)
                        if upload_function:
                            job_id = self.upload_scheduler.schedule_upload(
                                upload_task, 
                                upload_function
                            )
                            results['scheduled_uploads'].append({
                                'job_id': job_id,
                                'platform': platform,
                                'clip_path': optimized_path
                            })
            
            self.logger.info(f"Processing complete: {len(clips)} clips, {len(results['scheduled_uploads'])} uploads scheduled")
            return results
        
        except Exception as e:
            self.logger.error(f"Error processing video: {e}", exc_info=True)
            return results
    
    def _get_upload_function(self, platform):
        """Get upload function for platform"""
        uploaders = {
            'instagram': self.instagram_uploader.upload,
            'youtube': self.youtube_uploader.upload,
            'tiktok': self.tiktok_uploader.upload
        }
        return uploaders.get(platform)
    
    def process_all_videos(self, platforms=None, auto_upload=False):
        """Process all videos in input directory"""
        videos = self.discover_videos()
        
        if not videos:
            self.logger.warning("No videos found to process")
            return []
        
        results = []
        for video_path in videos:
            result = self.process_video(video_path, platforms, auto_upload)
            results.append(result)
        
        return results
    
    def start_scheduler(self):
        """Start the upload scheduler"""
        self.upload_scheduler.start()
        self.logger.info("Upload scheduler started")
    
    def stop_scheduler(self):
        """Stop the upload scheduler"""
        self.upload_scheduler.shutdown()
        self.logger.info("Upload scheduler stopped")


def main():
    """Main entry point with CLI"""
    parser = argparse.ArgumentParser(
        description='Autonomous Video Clipping and Publishing System'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process videos')
    process_parser.add_argument('--video', help='Specific video file to process')
    process_parser.add_argument('--platforms', nargs='+', 
                              choices=['instagram', 'youtube', 'tiktok'],
                              help='Platforms to upload to')
    process_parser.add_argument('--auto-upload', action='store_true',
                              help='Automatically schedule uploads')
    
    # Credentials command
    cred_parser = subparsers.add_parser('credentials', help='Manage credentials')
    cred_parser.add_argument('--platform', required=True,
                           choices=['instagram', 'youtube', 'tiktok', 'github_api'])
    cred_parser.add_argument('--field', required=True, help='Field name (username, password, etc.)')
    cred_parser.add_argument('--value', required=True, help='Field value')
    
    # Queue command
    queue_parser = subparsers.add_parser('queue', help='View upload queue')
    queue_parser.add_argument('--platform', help='Filter by platform')
    
    # History command
    history_parser = subparsers.add_parser('history', help='View upload history')
    history_parser.add_argument('--platform', help='Filter by platform')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of records')
    
    args = parser.parse_args()
    
    # Initialize system
    system = VideoClippingSystem()
    
    if args.command == 'process':
        # Start scheduler
        system.start_scheduler()
        
        try:
            if args.video:
                # Process specific video
                result = system.process_video(
                    args.video, 
                    args.platforms, 
                    args.auto_upload
                )
                print(f"\nProcessed: {args.video}")
                print(f"Clips extracted: {len(result['clips'])}")
                print(f"Uploads scheduled: {len(result['scheduled_uploads'])}")
            else:
                # Process all videos
                results = system.process_all_videos(args.platforms, args.auto_upload)
                print(f"\nProcessed {len(results)} videos")
                total_clips = sum(len(r['clips']) for r in results)
                total_uploads = sum(len(r['scheduled_uploads']) for r in results)
                print(f"Total clips extracted: {total_clips}")
                print(f"Total uploads scheduled: {total_uploads}")
            
            if args.auto_upload:
                print("\nScheduler is running. Press Ctrl+C to stop.")
                import time
                while True:
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
        finally:
            system.stop_scheduler()
    
    elif args.command == 'credentials':
        # Set credential
        system.credential_manager.encrypt_credential(
            args.platform, 
            args.field, 
            args.value
        )
        print(f"Credential set for {args.platform}.{args.field}")
    
    elif args.command == 'queue':
        # View queue
        queue = system.state_manager.get_queue(args.platform)
        print(f"\nUpload Queue ({len(queue)} tasks):")
        for task in queue:
            print(f"  - {task['clip_path']} -> {task['platform']} at {task.get('scheduled_time', 'N/A')}")
    
    elif args.command == 'history':
        # View history
        history = system.state_manager.get_history(
            platform=args.platform, 
            limit=args.limit
        )
        print(f"\nUpload History ({len(history)} records):")
        for record in history:
            print(f"  - {record['clip_path']} -> {record['platform']} ({record['status']}) at {record.get('upload_time', 'N/A')}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
