"""
Cloud Storage Integration Service
Handles Google Drive, Dropbox, and other cloud storage integrations
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import mimetypes

# Cloud storage client imports (install with pip)
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

try:
    import dropbox
    from dropbox.exceptions import AuthError, ApiError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

from services.cache_service import cache_service
from services.webhook_service import webhook_service

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    """Supported cloud storage providers"""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"  # Future implementation
    BOX = "box"  # Future implementation

class SyncStatus(Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class CloudFile:
    """Cloud storage file information"""
    id: str
    name: str
    path: str
    size: int
    mime_type: str
    modified_time: datetime
    created_time: datetime
    is_folder: bool
    parent_id: Optional[str] = None
    download_url: Optional[str] = None
    web_view_url: Optional[str] = None
    checksum: Optional[str] = None

@dataclass
class CloudCredentials:
    """Cloud storage credentials"""
    provider: CloudProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

@dataclass
class SyncConfiguration:
    """Sync configuration for cloud storage"""
    provider: CloudProvider
    folder_path: str
    sync_interval: int  # minutes
    auto_process: bool
    file_filters: List[str]  # file extensions to sync
    exclude_patterns: List[str]
    max_file_size: int  # bytes
    tags: List[str]

class GoogleDriveClient:
    """Google Drive API client"""
    
    def __init__(self, credentials: CloudCredentials):
        """Initialize Google Drive client"""
        if not GOOGLE_DRIVE_AVAILABLE:
            raise ImportError("Google Drive client libraries not available")
        
        self.credentials = credentials
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive service"""
        try:
            creds = Credentials(
                token=self.credentials.access_token,
                refresh_token=self.credentials.refresh_token,
                client_id=self.credentials.client_id,
                client_secret=self.credentials.client_secret
            )
            
            self.service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            raise
    
    async def list_files(self, folder_id: Optional[str] = None, 
                        query: Optional[str] = None) -> List[CloudFile]:
        """List files in Google Drive"""
        try:
            # Build query
            if not query:
                query = "trashed=false"
                if folder_id:
                    query += f" and '{folder_id}' in parents"
            
            # Execute query
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, parents, size, mimeType, modifiedTime, createdTime, webViewLink)"
            ).execute()
            
            files = []
            for item in results.get('files', []):
                cloud_file = CloudFile(
                    id=item['id'],
                    name=item['name'],
                    path=await self._get_file_path(item['id']),
                    size=int(item.get('size', 0)),
                    mime_type=item.get('mimeType', ''),
                    modified_time=self._parse_datetime(item.get('modifiedTime')),
                    created_time=self._parse_datetime(item.get('createdTime')),
                    is_folder=item.get('mimeType') == 'application/vnd.google-apps.folder',
                    parent_id=item.get('parents', [None])[0],
                    web_view_url=item.get('webViewLink')
                )
                files.append(cloud_file)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing Google Drive files: {str(e)}")
            raise
    
    async def download_file(self, file_id: str) -> bytes:
        """Download file from Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return file_io.getvalue()
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            raise
    
    async def get_file_info(self, file_id: str) -> CloudFile:
        """Get detailed file information"""
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, parents, size, mimeType, modifiedTime, createdTime, webViewLink, md5Checksum"
            ).execute()
            
            return CloudFile(
                id=file_info['id'],
                name=file_info['name'],
                path=await self._get_file_path(file_id),
                size=int(file_info.get('size', 0)),
                mime_type=file_info.get('mimeType', ''),
                modified_time=self._parse_datetime(file_info.get('modifiedTime')),
                created_time=self._parse_datetime(file_info.get('createdTime')),
                is_folder=file_info.get('mimeType') == 'application/vnd.google-apps.folder',
                parent_id=file_info.get('parents', [None])[0],
                web_view_url=file_info.get('webViewLink'),
                checksum=file_info.get('md5Checksum')
            )
            
        except Exception as e:
            logger.error(f"Error getting file info {file_id}: {str(e)}")
            raise
    
    async def _get_file_path(self, file_id: str) -> str:
        """Get full path of a file"""
        try:
            # This is a simplified implementation
            # In production, you'd want to build the full path by traversing parents
            file_info = self.service.files().get(fileId=file_id, fields="name, parents").execute()
            return f"/{file_info['name']}"
        except Exception:
            return "/unknown"
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse Google Drive datetime string"""
        try:
            from datetime import datetime
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return datetime.utcnow()

class DropboxClient:
    """Dropbox API client"""
    
    def __init__(self, credentials: CloudCredentials):
        """Initialize Dropbox client"""
        if not DROPBOX_AVAILABLE:
            raise ImportError("Dropbox client libraries not available")
        
        self.credentials = credentials
        self.client = dropbox.Dropbox(credentials.access_token)
    
    async def list_files(self, folder_path: str = "") -> List[CloudFile]:
        """List files in Dropbox"""
        try:
            result = self.client.files_list_folder(folder_path)
            files = []
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    cloud_file = CloudFile(
                        id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=entry.size,
                        mime_type=mimetypes.guess_type(entry.name)[0] or 'application/octet-stream',
                        modified_time=entry.server_modified,
                        created_time=entry.server_modified,  # Dropbox doesn't have separate created time
                        is_folder=False,
                        checksum=entry.content_hash
                    )
                    files.append(cloud_file)
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    cloud_file = CloudFile(
                        id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=0,
                        mime_type='application/vnd.dropbox.folder',
                        modified_time=datetime.utcnow(),
                        created_time=datetime.utcnow(),
                        is_folder=True
                    )
                    files.append(cloud_file)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing Dropbox files: {str(e)}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Dropbox"""
        try:
            metadata, response = self.client.files_download(file_path)
            return response.content
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {str(e)}")
            raise
    
    async def get_file_info(self, file_path: str) -> CloudFile:
        """Get detailed file information"""
        try:
            metadata = self.client.files_get_metadata(file_path)
            
            if isinstance(metadata, dropbox.files.FileMetadata):
                return CloudFile(
                    id=metadata.id,
                    name=metadata.name,
                    path=metadata.path_display,
                    size=metadata.size,
                    mime_type=mimetypes.guess_type(metadata.name)[0] or 'application/octet-stream',
                    modified_time=metadata.server_modified,
                    created_time=metadata.server_modified,
                    is_folder=False,
                    checksum=metadata.content_hash
                )
            else:
                raise ValueError("Path is not a file")
                
        except Exception as e:
            logger.error(f"Error getting file info {file_path}: {str(e)}")
            raise

class CloudStorageService:
    """Main cloud storage integration service"""
    
    def __init__(self):
        """Initialize cloud storage service"""
        self.cache = cache_service
        self.clients: Dict[str, Any] = {}  # user_id -> {provider -> client}
        self.sync_tasks: Dict[str, asyncio.Task] = {}  # user_id -> sync task
        
        logger.info("☁️  Cloud Storage Service initialized")
    
    async def connect_provider(self, user_id: str, provider: CloudProvider, 
                             credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a cloud storage provider"""
        try:
            # Create credentials object
            cloud_creds = CloudCredentials(
                provider=provider,
                access_token=credentials['access_token'],
                refresh_token=credentials.get('refresh_token'),
                expires_at=credentials.get('expires_at'),
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret')
            )
            
            # Initialize client
            if provider == CloudProvider.GOOGLE_DRIVE:
                client = GoogleDriveClient(cloud_creds)
            elif provider == CloudProvider.DROPBOX:
                client = DropboxClient(cloud_creds)
            else:
                raise ValueError(f"Provider {provider.value} not supported yet")
            
            # Store client
            if user_id not in self.clients:
                self.clients[user_id] = {}
            self.clients[user_id][provider] = client
            
            # Cache credentials (encrypted in production)
            creds_key = f"cloud_creds:{user_id}:{provider.value}"
            self.cache.set(creds_key, credentials, expire_seconds=86400 * 30)  # 30 days
            
            # Test connection
            test_files = await client.list_files()
            
            return {
                "message": f"Successfully connected to {provider.value}",
                "provider": provider.value,
                "test_files_count": len(test_files),
                "connected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error connecting to {provider.value}: {str(e)}")
            raise
    
    async def configure_sync(self, user_id: str, provider: CloudProvider, 
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure automatic sync for a provider"""
        try:
            # Validate configuration
            required_fields = ['folder_path', 'sync_interval', 'file_filters']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            sync_config = SyncConfiguration(
                provider=provider,
                folder_path=config['folder_path'],
                sync_interval=config['sync_interval'],
                auto_process=config.get('auto_process', True),
                file_filters=config['file_filters'],
                exclude_patterns=config.get('exclude_patterns', []),
                max_file_size=config.get('max_file_size', 50 * 1024 * 1024),  # 50MB default
                tags=config.get('tags', ['cloud-sync'])
            )
            
            # Store configuration
            config_key = f"sync_config:{user_id}:{provider.value}"
            config_data = {
                'provider': provider.value,
                'folder_path': sync_config.folder_path,
                'sync_interval': sync_config.sync_interval,
                'auto_process': sync_config.auto_process,
                'file_filters': sync_config.file_filters,
                'exclude_patterns': sync_config.exclude_patterns,
                'max_file_size': sync_config.max_file_size,
                'tags': sync_config.tags
            }
            self.cache.set(config_key, config_data, expire_seconds=86400 * 30)
            
            # Start sync task if not already running
            await self._start_sync_task(user_id, provider, sync_config)
            
            return {
                "message": f"Sync configured for {provider.value}",
                "configuration": config_data,
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error configuring sync: {str(e)}")
            raise
    
    async def manual_sync(self, user_id: str, provider: CloudProvider, 
                         folder_path: Optional[str] = None) -> Dict[str, Any]:
        """Manually trigger sync for a provider"""
        try:
            # Get client
            client = await self._get_client(user_id, provider)
            if not client:
                raise ValueError(f"Not connected to {provider.value}")
            
            # Get sync configuration
            sync_config = await self._get_sync_config(user_id, provider)
            if not sync_config:
                raise ValueError(f"Sync not configured for {provider.value}")
            
            # Use provided folder path or configured one
            target_folder = folder_path or sync_config['folder_path']
            
            # Perform sync
            sync_result = await self._perform_sync(user_id, client, sync_config, target_folder)
            
            return {
                "message": "Manual sync completed",
                "provider": provider.value,
                "folder_path": target_folder,
                "sync_result": sync_result,
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual sync: {str(e)}")
            raise
    
    async def list_cloud_files(self, user_id: str, provider: CloudProvider, 
                              folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files from cloud storage"""
        try:
            client = await self._get_client(user_id, provider)
            if not client:
                raise ValueError(f"Not connected to {provider.value}")
            
            # List files
            if provider == CloudProvider.GOOGLE_DRIVE:
                files = await client.list_files(folder_id=folder_path)
            else:  # Dropbox
                files = await client.list_files(folder_path or "")
            
            # Convert to dict format
            file_list = []
            for file in files:
                file_dict = {
                    "id": file.id,
                    "name": file.name,
                    "path": file.path,
                    "size": file.size,
                    "mime_type": file.mime_type,
                    "modified_time": file.modified_time.isoformat(),
                    "created_time": file.created_time.isoformat(),
                    "is_folder": file.is_folder,
                    "web_view_url": file.web_view_url
                }
                file_list.append(file_dict)
            
            return file_list
            
        except Exception as e:
            logger.error(f"Error listing cloud files: {str(e)}")
            raise
    
    async def download_and_process(self, user_id: str, provider: CloudProvider, 
                                 file_id: str, auto_process: bool = True) -> Dict[str, Any]:
        """Download and process a specific file"""
        try:
            client = await self._get_client(user_id, provider)
            if not client:
                raise ValueError(f"Not connected to {provider.value}")
            
            # Get file info
            if provider == CloudProvider.GOOGLE_DRIVE:
                file_info = await client.get_file_info(file_id)
                file_content = await client.download_file(file_id)
            else:  # Dropbox
                file_info = await client.get_file_info(file_id)
                file_content = await client.download_file(file_id)
            
            # Check file size
            if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
                raise ValueError("File too large (max 50MB)")
            
            # Process file if requested
            if auto_process:
                # Here you would integrate with your document processing service
                # For now, we'll simulate the processing
                document_id = f"cloud_{provider.value}_{file_id}"
                
                # Trigger webhook
                await webhook_service.trigger_webhook(
                    event_type="document.uploaded",
                    payload={
                        "document_id": document_id,
                        "filename": file_info.name,
                        "user_id": user_id,
                        "source": f"cloud_sync_{provider.value}",
                        "file_size": len(file_content),
                        "mime_type": file_info.mime_type,
                        "cloud_file_id": file_id,
                        "cloud_path": file_info.path
                    },
                    user_id=user_id
                )
                
                return {
                    "message": "File downloaded and processed successfully",
                    "document_id": document_id,
                    "file_info": {
                        "name": file_info.name,
                        "size": len(file_content),
                        "mime_type": file_info.mime_type,
                        "path": file_info.path
                    },
                    "processed_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "message": "File downloaded successfully",
                    "file_info": {
                        "name": file_info.name,
                        "size": len(file_content),
                        "mime_type": file_info.mime_type,
                        "path": file_info.path
                    },
                    "content": file_content.decode('utf-8', errors='ignore')[:1000] + "..." if len(file_content) > 1000 else file_content.decode('utf-8', errors='ignore'),
                    "downloaded_at": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error downloading and processing file: {str(e)}")
            raise
    
    async def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get sync status for all connected providers"""
        try:
            status = {
                "user_id": user_id,
                "providers": {},
                "active_syncs": 0,
                "last_sync": None
            }
            
            # Check each provider
            for provider in CloudProvider:
                provider_status = {
                    "connected": False,
                    "sync_configured": False,
                    "sync_active": False,
                    "last_sync": None,
                    "sync_interval": None,
                    "files_synced": 0
                }
                
                # Check connection
                if user_id in self.clients and provider in self.clients[user_id]:
                    provider_status["connected"] = True
                
                # Check sync configuration
                sync_config = await self._get_sync_config(user_id, provider)
                if sync_config:
                    provider_status["sync_configured"] = True
                    provider_status["sync_interval"] = sync_config["sync_interval"]
                
                # Check active sync
                sync_key = f"{user_id}_{provider.value}"
                if sync_key in self.sync_tasks and not self.sync_tasks[sync_key].done():
                    provider_status["sync_active"] = True
                    status["active_syncs"] += 1
                
                # Get last sync time
                last_sync_key = f"last_sync:{user_id}:{provider.value}"
                last_sync = self.cache.get(last_sync_key)
                if last_sync:
                    provider_status["last_sync"] = last_sync
                    if not status["last_sync"] or last_sync > status["last_sync"]:
                        status["last_sync"] = last_sync
                
                status["providers"][provider.value] = provider_status
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            raise
    
    async def disconnect_provider(self, user_id: str, provider: CloudProvider) -> Dict[str, Any]:
        """Disconnect from a cloud storage provider"""
        try:
            # Stop sync task
            sync_key = f"{user_id}_{provider.value}"
            if sync_key in self.sync_tasks:
                self.sync_tasks[sync_key].cancel()
                del self.sync_tasks[sync_key]
            
            # Remove client
            if user_id in self.clients and provider in self.clients[user_id]:
                del self.clients[user_id][provider]
            
            # Clear cached data
            creds_key = f"cloud_creds:{user_id}:{provider.value}"
            config_key = f"sync_config:{user_id}:{provider.value}"
            last_sync_key = f"last_sync:{user_id}:{provider.value}"
            
            self.cache.delete(creds_key)
            self.cache.delete(config_key)
            self.cache.delete(last_sync_key)
            
            return {
                "message": f"Disconnected from {provider.value}",
                "provider": provider.value,
                "disconnected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting from provider: {str(e)}")
            raise
    
    async def _get_client(self, user_id: str, provider: CloudProvider):
        """Get client for user and provider"""
        if user_id in self.clients and provider in self.clients[user_id]:
            return self.clients[user_id][provider]
        
        # Try to restore from cache
        creds_key = f"cloud_creds:{user_id}:{provider.value}"
        credentials = self.cache.get(creds_key)
        if credentials:
            try:
                await self.connect_provider(user_id, provider, credentials)
                return self.clients[user_id][provider]
            except Exception:
                pass
        
        return None
    
    async def _get_sync_config(self, user_id: str, provider: CloudProvider) -> Optional[Dict[str, Any]]:
        """Get sync configuration for user and provider"""
        config_key = f"sync_config:{user_id}:{provider.value}"
        return self.cache.get(config_key)
    
    async def _start_sync_task(self, user_id: str, provider: CloudProvider, 
                             sync_config: SyncConfiguration):
        """Start background sync task"""
        sync_key = f"{user_id}_{provider.value}"
        
        # Cancel existing task
        if sync_key in self.sync_tasks:
            self.sync_tasks[sync_key].cancel()
        
        # Start new task
        self.sync_tasks[sync_key] = asyncio.create_task(
            self._sync_loop(user_id, provider, sync_config)
        )
    
    async def _sync_loop(self, user_id: str, provider: CloudProvider, 
                        sync_config: SyncConfiguration):
        """Background sync loop"""
        while True:
            try:
                client = await self._get_client(user_id, provider)
                if client:
                    config_dict = {
                        'folder_path': sync_config.folder_path,
                        'auto_process': sync_config.auto_process,
                        'file_filters': sync_config.file_filters,
                        'exclude_patterns': sync_config.exclude_patterns,
                        'max_file_size': sync_config.max_file_size,
                        'tags': sync_config.tags
                    }
                    
                    await self._perform_sync(user_id, client, config_dict, sync_config.folder_path)
                
                # Wait for next sync
                await asyncio.sleep(sync_config.sync_interval * 60)  # Convert minutes to seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _perform_sync(self, user_id: str, client: Any, config: Dict[str, Any], 
                          folder_path: str) -> Dict[str, Any]:
        """Perform actual sync operation"""
        try:
            # List files
            if hasattr(client, 'list_files'):
                files = await client.list_files(folder_path)
            else:
                files = []
            
            # Filter files
            filtered_files = []
            for file in files:
                if file.is_folder:
                    continue
                
                # Check file extension
                if config['file_filters']:
                    file_ext = os.path.splitext(file.name)[1].lower()
                    if file_ext not in config['file_filters']:
                        continue
                
                # Check exclude patterns
                if any(pattern in file.name for pattern in config['exclude_patterns']):
                    continue
                
                # Check file size
                if file.size > config['max_file_size']:
                    continue
                
                filtered_files.append(file)
            
            # Process new/modified files
            processed_count = 0
            for file in filtered_files:
                try:
                    # Check if file was already processed
                    file_key = f"processed_file:{user_id}:{file.checksum or file.id}"
                    if self.cache.get(file_key):
                        continue
                    
                    # Download and process
                    if config['auto_process']:
                        await self.download_and_process(
                            user_id=user_id,
                            provider=CloudProvider.GOOGLE_DRIVE if hasattr(client, 'service') else CloudProvider.DROPBOX,
                            file_id=file.id,
                            auto_process=True
                        )
                        processed_count += 1
                        
                        # Mark as processed
                        self.cache.set(file_key, True, expire_seconds=86400 * 7)  # 7 days
                
                except Exception as e:
                    logger.error(f"Error processing file {file.name}: {str(e)}")
            
            # Update last sync time
            last_sync_key = f"last_sync:{user_id}:{client.__class__.__name__.replace('Client', '').lower()}"
            self.cache.set(last_sync_key, datetime.utcnow().isoformat(), expire_seconds=86400 * 30)
            
            return {
                "total_files": len(files),
                "filtered_files": len(filtered_files),
                "processed_files": processed_count,
                "sync_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error performing sync: {str(e)}")
            raise

# Global cloud storage service instance
cloud_storage_service = CloudStorageService()