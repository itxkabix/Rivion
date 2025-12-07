import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
import shutil
from app.config import settings

logger = logging.getLogger(__name__)

class LocalImageStorage:
    """Handle local file storage for images"""
    
    def __init__(self):
        self.base_dir = settings.STORAGE_DIR
        self._create_directories()
    
    def _create_directories(self):
        """Create storage directories if they don't exist"""
        dirs = [
            self.base_dir,
            os.path.join(self.base_dir, 'sessions'),
            os.path.join(self.base_dir, 'faces'),
            os.path.join(self.base_dir, 'emotions'),
            os.path.join(self.base_dir, 'temp')
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory ready: {dir_path}")
    
    def save_session_image(self, image_data: bytes, session_id: str) -> str:
        """Save session captured image"""
        try:
            session_dir = os.path.join(self.base_dir, 'sessions', session_id)
            Path(session_dir).mkdir(parents=True, exist_ok=True)
            
            filename = f"captured_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(session_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"✅ Session image saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Error saving session image: {e}")
            raise
    
    def save_face_crop(self, image_data: bytes, session_id: str, face_id: str) -> str:
        """Save cropped face image"""
        try:
            faces_dir = os.path.join(self.base_dir, 'faces', session_id)
            Path(faces_dir).mkdir(parents=True, exist_ok=True)
            
            filename = f"face_{face_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(faces_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"✅ Face crop saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Error saving face crop: {e}")
            raise
    
    def get_session_files(self, session_id: str) -> list:
        """Get all files for a session"""
        try:
            session_dir = os.path.join(self.base_dir, 'sessions', session_id)
            if not os.path.exists(session_dir):
                return []
            
            files = []
            for filename in os.listdir(session_dir):
                filepath = os.path.join(session_dir, filename)
                files.append({
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath)
                })
            
            return files
        except Exception as e:
            logger.error(f"Error getting session files: {e}")
            return []
    
    def delete_session_files(self, session_id: str) -> bool:
        """Delete all files for a session (privacy)"""
        try:
            session_dir = os.path.join(self.base_dir, 'sessions', session_id)
            faces_dir = os.path.join(self.base_dir, 'faces', session_id)
            
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                logger.info(f"✅ Deleted session directory: {session_dir}")
            
            if os.path.exists(faces_dir):
                shutil.rmtree(faces_dir)
                logger.info(f"✅ Deleted faces directory: {faces_dir}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting session files: {e}")
            return False
    
    def cleanup_old_sessions(self, hours: int = 24) -> int:
        """Delete sessions older than specified hours"""
        try:
            from datetime import datetime, timedelta
            import time
            
            session_dir = os.path.join(self.base_dir, 'sessions')
            cutoff_time = time.time() - (hours * 3600)
            deleted_count = 0
            
            if os.path.exists(session_dir):
                for session_id in os.listdir(session_dir):
                    session_path = os.path.join(session_dir, session_id)
                    if os.path.isdir(session_path):
                        mod_time = os.path.getmtime(session_path)
                        if mod_time < cutoff_time:
                            shutil.rmtree(session_path)
                            deleted_count += 1
                            logger.info(f"🧹 Cleanup: Deleted old session {session_id}")
            
            logger.info(f"🧹 Cleanup complete: Deleted {deleted_count} old sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

# Singleton instance
storage = LocalImageStorage()

# Public functions
async def save_session_image(image_data: bytes, session_id: str) -> str:
    return storage.save_session_image(image_data, session_id)

async def save_face_crop(image_data: bytes, session_id: str, face_id: str) -> str:
    return storage.save_face_crop(image_data, session_id, face_id)

async def get_session_files(session_id: str) -> list:
    return storage.get_session_files(session_id)

async def delete_session_files(session_id: str) -> bool:
    return storage.delete_session_files(session_id)

async def cleanup_old_sessions(hours: int = 24) -> int:
    return storage.cleanup_old_sessions(hours)
