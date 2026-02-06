"""
Upload Scheduler - Manage scheduled uploads using APScheduler
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)


class UploadScheduler:
    """Schedule and manage delayed uploads"""
    
    def __init__(self, config, state_manager):
        """
        Initialize upload scheduler
        
        Args:
            config: Scheduling configuration dictionary
            state_manager: StateManager instance
        """
        self.config = config
        self.state_manager = state_manager
        self.scheduler = BackgroundScheduler()
        self.min_delay_minutes = config.get('min_upload_delay_minutes', 60)
        self.stagger_uploads = config.get('stagger_uploads', True)
        self.stagger_delay_minutes = config.get('stagger_delay_minutes', 5)
        self.max_retry_attempts = config.get('max_retry_attempts', 3)
        self.retry_delay_minutes = config.get('retry_delay_minutes', 15)
        
        # Track scheduled jobs
        self.scheduled_jobs = {}
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Upload scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Upload scheduler stopped")
    
    def _get_next_upload_time(self, platform):
        """
        Calculate next available upload time for platform
        
        Args:
            platform: Platform name
            
        Returns:
            datetime object for next upload time
        """
        # Get last upload time from state
        last_upload_time = self.state_manager.get_last_upload_time(platform)
        
        if last_upload_time:
            last_upload = datetime.fromisoformat(last_upload_time)
            min_next_time = last_upload + timedelta(minutes=self.min_delay_minutes)
            
            # If minimum time hasn't passed, use it
            if min_next_time > datetime.now():
                return min_next_time
        
        # Otherwise, schedule for now (or very soon)
        return datetime.now() + timedelta(seconds=10)
    
    def schedule_upload(self, upload_task, upload_function):
        """
        Schedule an upload task
        
        Args:
            upload_task: Dictionary containing upload details
            upload_function: Function to call for upload (receives upload_task as parameter)
            
        Returns:
            Scheduled job ID
        """
        clip_path = upload_task.get('clip_path')
        platform = upload_task.get('platform')
        
        # Calculate upload time
        scheduled_time = upload_task.get('scheduled_time')
        
        if scheduled_time:
            # Use provided schedule time
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time)
        else:
            # Calculate next available time
            scheduled_time = self._get_next_upload_time(platform)
            upload_task['scheduled_time'] = scheduled_time.isoformat()
        
        # Ensure scheduled time is in the future
        if scheduled_time <= datetime.now():
            scheduled_time = datetime.now() + timedelta(seconds=10)
            upload_task['scheduled_time'] = scheduled_time.isoformat()
        
        # Create job ID
        job_id = f"{platform}_{clip_path.replace('/', '_')}_{int(scheduled_time.timestamp())}"
        
        # Add to queue
        self.state_manager.add_to_queue(upload_task)
        
        # Schedule job
        job = self.scheduler.add_job(
            func=self._execute_upload,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[upload_task, upload_function],
            id=job_id,
            replace_existing=True
        )
        
        self.scheduled_jobs[job_id] = {
            'job': job,
            'task': upload_task,
            'scheduled_time': scheduled_time
        }
        
        logger.info(f"Scheduled upload for {platform} at {scheduled_time}: {clip_path}")
        return job_id
    
    def _execute_upload(self, upload_task, upload_function):
        """
        Execute an upload task with retry logic
        
        Args:
            upload_task: Upload task dictionary
            upload_function: Upload function to call
        """
        clip_path = upload_task.get('clip_path')
        platform = upload_task.get('platform')
        
        logger.info(f"Executing upload: {clip_path} -> {platform}")
        
        retry_count = upload_task.get('retry_count', 0)
        
        try:
            # Call upload function
            success = upload_function(upload_task)
            
            if success:
                # Upload successful
                logger.info(f"Upload successful: {clip_path} -> {platform}")
                
                # Add to history
                self.state_manager.add_to_history({
                    'video_path': upload_task.get('video_path'),
                    'clip_path': clip_path,
                    'platform': platform,
                    'status': 'success',
                    'upload_time': datetime.now().isoformat(),
                    'metadata': upload_task.get('metadata', {})
                })
                
                # Remove from queue
                self.state_manager.remove_from_queue(clip_path, platform)
            else:
                # Upload failed
                logger.error(f"Upload failed: {clip_path} -> {platform}")
                self._handle_failed_upload(upload_task, upload_function)
        
        except Exception as e:
            logger.error(f"Upload error: {e}")
            self._handle_failed_upload(upload_task, upload_function)
    
    def _handle_failed_upload(self, upload_task, upload_function):
        """
        Handle failed upload with retry logic
        
        Args:
            upload_task: Upload task dictionary
            upload_function: Upload function to call
        """
        clip_path = upload_task.get('clip_path')
        platform = upload_task.get('platform')
        retry_count = upload_task.get('retry_count', 0)
        
        if retry_count < self.max_retry_attempts:
            # Schedule retry
            retry_count += 1
            upload_task['retry_count'] = retry_count
            
            retry_time = datetime.now() + timedelta(minutes=self.retry_delay_minutes)
            upload_task['scheduled_time'] = retry_time.isoformat()
            
            logger.info(f"Scheduling retry {retry_count}/{self.max_retry_attempts} at {retry_time}")
            
            # Update queue
            self.state_manager.update_queue_task(clip_path, platform, upload_task)
            
            # Schedule retry
            self.schedule_upload(upload_task, upload_function)
        else:
            # Max retries reached
            logger.error(f"Max retries reached for {clip_path} -> {platform}")
            
            # Add to history as failed
            self.state_manager.add_to_history({
                'video_path': upload_task.get('video_path'),
                'clip_path': clip_path,
                'platform': platform,
                'status': 'failed',
                'upload_time': datetime.now().isoformat(),
                'metadata': upload_task.get('metadata', {}),
                'error': 'Max retries exceeded'
            })
            
            # Remove from queue
            self.state_manager.remove_from_queue(clip_path, platform)
    
    def schedule_batch_upload(self, upload_tasks, upload_functions):
        """
        Schedule multiple uploads with staggering
        
        Args:
            upload_tasks: List of upload task dictionaries
            upload_functions: Dictionary mapping platform names to upload functions
            
        Returns:
            List of job IDs
        """
        job_ids = []
        current_time = datetime.now()
        
        for i, task in enumerate(upload_tasks):
            platform = task.get('platform')
            upload_function = upload_functions.get(platform)
            
            if not upload_function:
                logger.error(f"No upload function for platform: {platform}")
                continue
            
            # Calculate staggered time
            if self.stagger_uploads and i > 0:
                delay_minutes = i * self.stagger_delay_minutes
                scheduled_time = current_time + timedelta(minutes=delay_minutes)
                
                # Ensure minimum delay from last upload
                next_available = self._get_next_upload_time(platform)
                if scheduled_time < next_available:
                    scheduled_time = next_available
                
                task['scheduled_time'] = scheduled_time.isoformat()
            
            # Schedule upload
            job_id = self.schedule_upload(task, upload_function)
            job_ids.append(job_id)
        
        logger.info(f"Scheduled {len(job_ids)} uploads")
        return job_ids
    
    def cancel_upload(self, job_id):
        """
        Cancel a scheduled upload
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        if job_id in self.scheduled_jobs:
            try:
                self.scheduler.remove_job(job_id)
                
                task = self.scheduled_jobs[job_id]['task']
                self.state_manager.remove_from_queue(
                    task.get('clip_path'),
                    task.get('platform')
                )
                
                del self.scheduled_jobs[job_id]
                
                logger.info(f"Cancelled upload: {job_id}")
                return True
            
            except Exception as e:
                logger.error(f"Failed to cancel upload: {e}")
        
        return False
    
    def get_scheduled_uploads(self):
        """
        Get list of scheduled uploads
        
        Returns:
            List of scheduled job information
        """
        return [
            {
                'job_id': job_id,
                'clip_path': info['task'].get('clip_path'),
                'platform': info['task'].get('platform'),
                'scheduled_time': info['scheduled_time'].isoformat()
            }
            for job_id, info in self.scheduled_jobs.items()
        ]
