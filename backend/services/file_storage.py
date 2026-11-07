"""
Clean File storage service
"""

from typing import Dict, Any, Optional
import os
import hashlib

class FileStorageService:
    """Service for file storage operations (simplified version)"""
    
    def __init__(self):
        """Initialize file storage service"""
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def store_file(self, user_id: str, filename: str, file_content: bytes) -> Dict[str, Any]:
        """Store a file and return storage info"""
        try:
            # Create user directory
            user_dir = os.path.join(self.upload_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate file hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Create file path
            file_path = os.path.join(user_dir, filename)
            
            # Check if file already exists
            is_duplicate = os.path.exists(file_path)
            
            # Store file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return {
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size": len(file_content),
                "is_duplicate": is_duplicate,
                "content_type": self._detect_content_type(filename)
            }
            
        except Exception as e:
            print(f"Error storing file: {str(e)}")
            return None
    
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"Error retrieving file: {str(e)}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def get_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get storage statistics for a user"""
        try:
            user_dir = os.path.join(self.upload_dir, user_id)
            if not os.path.exists(user_dir):
                return {"total_files": 0, "total_size": 0}
            
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(user_dir):
                total_files += len(files)
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            print(f"Error getting storage stats: {str(e)}")
            return {"total_files": 0, "total_size": 0}
    
    def _detect_content_type(self, filename: str) -> str:
        """Detect content type from filename"""
        if not filename:
            return "application/octet-stream"
        
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        content_types = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'json': 'application/json',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'py': 'text/x-python',
            'java': 'text/x-java-source',
            'cpp': 'text/x-c++src',
            'c': 'text/x-csrc',
            'xml': 'application/xml',
            'csv': 'text/csv',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif'
        }
        
        return content_types.get(ext, 'application/octet-stream')

# Global file storage service instance
file_storage = FileStorageService()