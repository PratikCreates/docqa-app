"""
File storage service for handling document uploads and storage
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import mimetypes

class FileStorageService:
    """Service for handling file storage and retrieval"""
    
    def __init__(self, storage_root: str = "storage"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.documents_dir = self.storage_root / "documents"
        self.temp_dir = self.storage_root / "temp"
        self.thumbnails_dir = self.storage_root / "thumbnails"
        
        for directory in [self.documents_dir, self.temp_dir, self.thumbnails_dir]:
            directory.mkdir(exist_ok=True)
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _get_file_path(self, user_id: str, file_hash: str, filename: str) -> Path:
        """Generate organized file path based on user ID and file hash"""
        # Create user directory
        user_dir = self.documents_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        # Create subdirectory based on first 2 characters of hash for better organization
        hash_prefix = file_hash[:2]
        hash_dir = user_dir / hash_prefix
        hash_dir.mkdir(exist_ok=True)
        
        # Use hash as filename with original extension
        file_extension = Path(filename).suffix
        stored_filename = f"{file_hash}{file_extension}"
        
        return hash_dir / stored_filename
    
    def store_file(self, user_id: str, filename: str, file_content: bytes) -> Dict[str, Any]:
        """
        Store a file and return storage information
        
        Returns:
            Dict containing file_path, file_hash, file_size, and content_type
        """
        try:
            # Generate file hash
            file_hash = self._generate_file_hash(file_content)
            
            # Get storage path
            file_path = self._get_file_path(user_id, file_hash, filename)
            
            # Check if file already exists (deduplication)
            if file_path.exists():
                existing_size = file_path.stat().st_size
                if existing_size == len(file_content):
                    # File already exists and is identical
                    return {
                        "file_path": str(file_path.relative_to(self.storage_root)),
                        "file_hash": file_hash,
                        "file_size": len(file_content),
                        "content_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
                        "is_duplicate": True
                    }
            
            # Write file to storage
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return {
                "file_path": str(file_path.relative_to(self.storage_root)),
                "file_hash": file_hash,
                "file_size": len(file_content),
                "content_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
                "is_duplicate": False
            }
            
        except Exception as e:
            raise Exception(f"Failed to store file: {str(e)}")
    
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content by path"""
        try:
            full_path = self.storage_root / file_path
            if not full_path.exists():
                return None
            
            with open(full_path, "rb") as f:
                return f.read()
                
        except Exception as e:
            print(f"Error retrieving file {file_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            full_path = self.storage_root / file_path
            if full_path.exists():
                full_path.unlink()
                
                # Clean up empty directories
                parent_dir = full_path.parent
                if parent_dir != self.documents_dir and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            full_path = self.storage_root / file_path
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            return {
                "file_path": file_path,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "content_type": mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
            }
            
        except Exception as e:
            print(f"Error getting file info {file_path}: {str(e)}")
            return None
    
    def create_temp_file(self, filename: str, content: bytes) -> str:
        """Create a temporary file and return its path"""
        temp_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        temp_path = self.temp_dir / temp_filename
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        return str(temp_path.relative_to(self.storage_root))
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for temp_file in self.temp_dir.iterdir():
            if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                try:
                    temp_file.unlink()
                except Exception as e:
                    print(f"Error cleaning up temp file {temp_file}: {str(e)}")
    
    def get_storage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            if user_id:
                user_dir = self.documents_dir / str(user_id)
                if not user_dir.exists():
                    return {"total_files": 0, "total_size": 0}
                
                total_files = 0
                total_size = 0
                
                for file_path in user_dir.rglob("*"):
                    if file_path.is_file():
                        total_files += 1
                        total_size += file_path.stat().st_size
                
                return {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
            else:
                # Global stats
                total_files = 0
                total_size = 0
                
                for file_path in self.documents_dir.rglob("*"):
                    if file_path.is_file():
                        total_files += 1
                        total_size += file_path.stat().st_size
                
                return {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2)
                }
                
        except Exception as e:
            print(f"Error getting storage stats: {str(e)}")
            return {"total_files": 0, "total_size": 0}

# Global file storage service instance
file_storage = FileStorageService()