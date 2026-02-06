"""
State Manager - Manage JSON state files for upload tracking
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class StateManager:
    """Manage upload history and queue state"""
    
    def __init__(self, state_dir="cache"):
        """
        Initialize state manager
        
        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = state_dir
        self.history_file = os.path.join(state_dir, "upload_history.json")
        self.queue_file = os.path.join(state_dir, "upload_queue.json")
        
        # Ensure state directory exists
        os.makedirs(state_dir, exist_ok=True)
        
        # Initialize state files if they don't exist
        self._init_state_files()
    
    def _init_state_files(self):
        """Initialize state files with empty structures"""
        if not os.path.exists(self.history_file):
            self._save_json(self.history_file, {
                "uploads": [],
                "last_updated": datetime.now().isoformat()
            })
        
        if not os.path.exists(self.queue_file):
            self._save_json(self.queue_file, {
                "queue": [],
                "last_updated": datetime.now().isoformat()
            })
    
    def _load_json(self, file_path):
        """Load JSON from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path, data):
        """Save JSON to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
    
    def add_to_history(self, upload_record: Dict[str, Any]):
        """
        Add upload record to history
        
        Args:
            upload_record: Dictionary containing upload details
                - video_path: Source video path
                - clip_path: Clip file path
                - platform: Platform name
                - upload_time: Upload timestamp
                - status: Upload status (success, failed, pending)
                - metadata: Caption, hashtags, etc.
        """
        history = self._load_json(self.history_file)
        
        # Add timestamp if not present
        if 'upload_time' not in upload_record:
            upload_record['upload_time'] = datetime.now().isoformat()
        
        history['uploads'].append(upload_record)
        history['last_updated'] = datetime.now().isoformat()
        
        self._save_json(self.history_file, history)
        logger.info(f"Added upload record to history: {upload_record.get('clip_path')} -> {upload_record.get('platform')}")
    
    def get_history(self, platform=None, status=None, limit=None):
        """
        Get upload history with optional filtering
        
        Args:
            platform: Filter by platform
            status: Filter by status
            limit: Limit number of results
            
        Returns:
            List of upload records
        """
        history = self._load_json(self.history_file)
        uploads = history.get('uploads', [])
        
        # Apply filters
        if platform:
            uploads = [u for u in uploads if u.get('platform') == platform]
        
        if status:
            uploads = [u for u in uploads if u.get('status') == status]
        
        # Sort by upload time (most recent first)
        uploads.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
        
        # Apply limit
        if limit:
            uploads = uploads[:limit]
        
        return uploads
    
    def add_to_queue(self, upload_task: Dict[str, Any]):
        """
        Add upload task to queue
        
        Args:
            upload_task: Dictionary containing task details
                - clip_path: Clip file path
                - platform: Platform name
                - scheduled_time: Scheduled upload time
                - metadata: Caption, hashtags, etc.
                - priority: Task priority (higher = more urgent)
        """
        queue = self._load_json(self.queue_file)
        
        # Add creation time if not present
        if 'created_time' not in upload_task:
            upload_task['created_time'] = datetime.now().isoformat()
        
        # Set default priority if not present
        if 'priority' not in upload_task:
            upload_task['priority'] = 0
        
        queue['queue'].append(upload_task)
        queue['last_updated'] = datetime.now().isoformat()
        
        self._save_json(self.queue_file, queue)
        logger.info(f"Added task to queue: {upload_task.get('clip_path')} -> {upload_task.get('platform')}")
    
    def get_queue(self, platform=None):
        """
        Get upload queue with optional filtering
        
        Args:
            platform: Filter by platform
            
        Returns:
            List of upload tasks sorted by priority and scheduled time
        """
        queue = self._load_json(self.queue_file)
        tasks = queue.get('queue', [])
        
        # Apply filters
        if platform:
            tasks = [t for t in tasks if t.get('platform') == platform]
        
        # Sort by priority (descending) then scheduled time (ascending)
        tasks.sort(key=lambda x: (
            -x.get('priority', 0),
            x.get('scheduled_time', datetime.now().isoformat())
        ))
        
        return tasks
    
    def remove_from_queue(self, clip_path: str, platform: str):
        """
        Remove task from queue
        
        Args:
            clip_path: Clip file path
            platform: Platform name
        """
        queue = self._load_json(self.queue_file)
        
        # Filter out the task
        queue['queue'] = [
            t for t in queue['queue']
            if not (t.get('clip_path') == clip_path and t.get('platform') == platform)
        ]
        queue['last_updated'] = datetime.now().isoformat()
        
        self._save_json(self.queue_file, queue)
        logger.info(f"Removed task from queue: {clip_path} -> {platform}")
    
    def update_queue_task(self, clip_path: str, platform: str, updates: Dict[str, Any]):
        """
        Update a task in the queue
        
        Args:
            clip_path: Clip file path
            platform: Platform name
            updates: Dictionary of fields to update
        """
        queue = self._load_json(self.queue_file)
        
        # Find and update the task
        for task in queue['queue']:
            if task.get('clip_path') == clip_path and task.get('platform') == platform:
                task.update(updates)
                break
        
        queue['last_updated'] = datetime.now().isoformat()
        self._save_json(self.queue_file, queue)
        logger.info(f"Updated task in queue: {clip_path} -> {platform}")
    
    def get_last_upload_time(self, platform: str):
        """
        Get the last upload time for a platform
        
        Args:
            platform: Platform name
            
        Returns:
            ISO formatted datetime string or None
        """
        history = self.get_history(platform=platform, status='success', limit=1)
        if history:
            return history[0].get('upload_time')
        return None
    
    def clear_history(self):
        """Clear upload history"""
        self._save_json(self.history_file, {
            "uploads": [],
            "last_updated": datetime.now().isoformat()
        })
        logger.info("Cleared upload history")
    
    def clear_queue(self):
        """Clear upload queue"""
        self._save_json(self.queue_file, {
            "queue": [],
            "last_updated": datetime.now().isoformat()
        })
        logger.info("Cleared upload queue")
