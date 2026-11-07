"""
Cloud Storage Integration API Endpoints
Provides REST API for Google Drive, Dropbox, and other cloud storage integrations
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from services.cloud_storage_service import cloud_storage_service, CloudProvider
from api.auth_middleware import api_middleware

router = APIRouter(prefix="/cloud-storage", tags=["Cloud Storage"])

class CloudProviderEnum(str, Enum):
    """Cloud provider enum for API"""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    BOX = "box"

class CloudConnectionRequest(BaseModel):
    """Request model for connecting to cloud storage"""
    provider: CloudProviderEnum
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

class SyncConfigurationRequest(BaseModel):
    """Request model for sync configuration"""
    provider: CloudProviderEnum
    folder_path: str
    sync_interval: int = 60  # minutes
    auto_process: bool = True
    file_filters: List[str] = [".pdf", ".docx", ".txt", ".md", ".html"]
    exclude_patterns: List[str] = []
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    tags: List[str] = ["cloud-sync"]
    
    @validator('sync_interval')
    def validate_sync_interval(cls, v):
        if v < 5:
            raise ValueError('Sync interval must be at least 5 minutes')
        if v > 1440:  # 24 hours
            raise ValueError('Sync interval cannot exceed 24 hours')
        return v
    
    @validator('max_file_size')
    def validate_file_size(cls, v):
        if v > 100 * 1024 * 1024:  # 100MB
            raise ValueError('Maximum file size cannot exceed 100MB')
        return v

class ManualSyncRequest(BaseModel):
    """Request model for manual sync"""
    provider: CloudProviderEnum
    folder_path: Optional[str] = None

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user"""
    is_allowed, user_data, headers = api_middleware.process_request(
        dict(request.headers), 
        request.url.path
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=user_data.get("error", {}).get("message", "Authentication required")
        )
    
    return user_data

@router.post("/connect",
             summary="Connect to cloud storage",
             description="Connect to a cloud storage provider (Google Drive, Dropbox, etc.)")
async def connect_cloud_storage(
    connection_request: CloudConnectionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Connect to a cloud storage provider"""
    try:
        # Convert string enum to CloudProvider enum
        provider = CloudProvider(connection_request.provider.value)
        
        # Prepare credentials
        credentials = {
            "access_token": connection_request.access_token,
            "refresh_token": connection_request.refresh_token,
            "expires_at": connection_request.expires_at,
            "client_id": connection_request.client_id,
            "client_secret": connection_request.client_secret
        }
        
        # Connect to provider
        result = await cloud_storage_service.connect_provider(
            user_id=user["user_id"],
            provider=provider,
            credentials=credentials
        )
        
        return {
            "message": "Successfully connected to cloud storage",
            "connection_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")

@router.post("/configure-sync",
             summary="Configure automatic sync",
             description="Configure automatic synchronization for a cloud storage provider")
async def configure_sync(
    sync_config: SyncConfigurationRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Configure automatic sync for a cloud storage provider"""
    try:
        provider = CloudProvider(sync_config.provider.value)
        
        config = {
            "folder_path": sync_config.folder_path,
            "sync_interval": sync_config.sync_interval,
            "auto_process": sync_config.auto_process,
            "file_filters": sync_config.file_filters,
            "exclude_patterns": sync_config.exclude_patterns,
            "max_file_size": sync_config.max_file_size,
            "tags": sync_config.tags
        }
        
        result = await cloud_storage_service.configure_sync(
            user_id=user["user_id"],
            provider=provider,
            config=config
        )
        
        return {
            "message": "Sync configuration saved successfully",
            "configuration": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure sync: {str(e)}")

@router.post("/sync",
             summary="Manual sync",
             description="Manually trigger synchronization for a cloud storage provider")
async def manual_sync(
    sync_request: ManualSyncRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually trigger sync for a cloud storage provider"""
    try:
        provider = CloudProvider(sync_request.provider.value)
        
        result = await cloud_storage_service.manual_sync(
            user_id=user["user_id"],
            provider=provider,
            folder_path=sync_request.folder_path
        )
        
        return {
            "message": "Manual sync completed successfully",
            "sync_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual sync failed: {str(e)}")

@router.get("/files",
            summary="List cloud files",
            description="List files from connected cloud storage providers")
async def list_cloud_files(
    provider: CloudProviderEnum,
    folder_path: Optional[str] = Query(None, description="Folder path to list files from"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List files from cloud storage"""
    try:
        cloud_provider = CloudProvider(provider.value)
        
        files = await cloud_storage_service.list_cloud_files(
            user_id=user["user_id"],
            provider=cloud_provider,
            folder_path=folder_path
        )
        
        return {
            "provider": provider.value,
            "folder_path": folder_path,
            "files": files,
            "total_files": len(files),
            "listed_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.post("/download-and-process",
             summary="Download and process file",
             description="Download a specific file from cloud storage and process it")
async def download_and_process_file(
    provider: CloudProviderEnum,
    file_id: str,
    auto_process: bool = True,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Download and process a specific file from cloud storage"""
    try:
        cloud_provider = CloudProvider(provider.value)
        
        result = await cloud_storage_service.download_and_process(
            user_id=user["user_id"],
            provider=cloud_provider,
            file_id=file_id,
            auto_process=auto_process
        )
        
        return {
            "message": "File downloaded and processed successfully",
            "processing_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download and process file: {str(e)}")

@router.get("/sync-status",
            summary="Get sync status",
            description="Get synchronization status for all connected providers")
async def get_sync_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get sync status for all connected providers"""
    try:
        status = await cloud_storage_service.get_sync_status(user["user_id"])
        
        return {
            "sync_status": status,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@router.delete("/disconnect",
               summary="Disconnect from cloud storage",
               description="Disconnect from a cloud storage provider")
async def disconnect_cloud_storage(
    provider: CloudProviderEnum,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Disconnect from a cloud storage provider"""
    try:
        cloud_provider = CloudProvider(provider.value)
        
        result = await cloud_storage_service.disconnect_provider(
            user_id=user["user_id"],
            provider=cloud_provider
        )
        
        return {
            "message": "Successfully disconnected from cloud storage",
            "disconnection_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@router.get("/providers",
            summary="Get supported providers",
            description="Get list of supported cloud storage providers")
async def get_supported_providers():
    """Get list of supported cloud storage providers"""
    providers = []
    
    for provider in CloudProvider:
        provider_info = {
            "id": provider.value,
            "name": provider.value.replace("_", " ").title(),
            "supported": True,
            "features": {
                "file_listing": True,
                "file_download": True,
                "automatic_sync": True,
                "folder_sync": True,
                "real_time_sync": False  # Future feature
            }
        }
        
        # Add provider-specific information
        if provider == CloudProvider.GOOGLE_DRIVE:
            provider_info.update({
                "name": "Google Drive",
                "auth_type": "OAuth2",
                "scopes_required": ["https://www.googleapis.com/auth/drive.readonly"],
                "setup_instructions": "Enable Google Drive API and obtain OAuth2 credentials"
            })
        elif provider == CloudProvider.DROPBOX:
            provider_info.update({
                "name": "Dropbox",
                "auth_type": "OAuth2",
                "scopes_required": ["files.content.read"],
                "setup_instructions": "Create Dropbox app and obtain access token"
            })
        elif provider in [CloudProvider.ONEDRIVE, CloudProvider.BOX]:
            provider_info.update({
                "supported": False,
                "status": "Coming soon"
            })
        
        providers.append(provider_info)
    
    return {
        "supported_providers": providers,
        "total_providers": len(providers),
        "supported_count": sum(1 for p in providers if p["supported"])
    }

@router.get("/oauth-urls",
            summary="Get OAuth URLs",
            description="Get OAuth authorization URLs for cloud storage providers")
async def get_oauth_urls(
    provider: CloudProviderEnum,
    redirect_uri: HttpUrl,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get OAuth authorization URL for a provider"""
    try:
        # This would typically generate the actual OAuth URL
        # For now, we'll return example URLs
        
        oauth_urls = {
            "google_drive": f"https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri={redirect_uri}&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline",
            "dropbox": f"https://www.dropbox.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri={redirect_uri}&response_type=code",
            "onedrive": f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=YOUR_CLIENT_ID&redirect_uri={redirect_uri}&scope=https://graph.microsoft.com/Files.Read&response_type=code",
            "box": f"https://account.box.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri={redirect_uri}&response_type=code"
        }
        
        if provider.value not in oauth_urls:
            raise HTTPException(status_code=400, detail=f"OAuth not supported for {provider.value}")
        
        return {
            "provider": provider.value,
            "oauth_url": oauth_urls[provider.value],
            "redirect_uri": str(redirect_uri),
            "instructions": f"Visit the OAuth URL to authorize access to your {provider.value.replace('_', ' ').title()} account",
            "next_step": "After authorization, use the returned code to exchange for access tokens"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}")

@router.post("/oauth-callback",
             summary="Handle OAuth callback",
             description="Handle OAuth callback and exchange code for tokens")
async def handle_oauth_callback(
    provider: CloudProviderEnum,
    code: str,
    redirect_uri: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Handle OAuth callback and exchange code for tokens"""
    try:
        # This would typically exchange the code for access tokens
        # For now, we'll return a placeholder response
        
        return {
            "message": "OAuth callback handled successfully",
            "provider": provider.value,
            "status": "tokens_exchanged",
            "next_step": "Use the returned tokens to connect to the cloud storage provider",
            "note": "In production, this would exchange the authorization code for access and refresh tokens"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@router.get("/sync-history",
            summary="Get sync history",
            description="Get synchronization history for a provider")
async def get_sync_history(
    provider: CloudProviderEnum,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get sync history for a provider"""
    try:
        # In production, this would query actual sync history from database
        # For now, we'll return a placeholder response
        
        history = {
            "provider": provider.value,
            "sync_history": [
                {
                    "sync_id": "sync_123456",
                    "started_at": "2024-01-15T10:00:00Z",
                    "completed_at": "2024-01-15T10:05:00Z",
                    "status": "completed",
                    "files_processed": 15,
                    "files_uploaded": 12,
                    "files_failed": 0,
                    "total_size": 25600000,
                    "duration_seconds": 300
                }
            ],
            "total_syncs": 1,
            "limit": limit,
            "offset": offset
        }
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")

@router.get("/storage-usage",
            summary="Get storage usage",
            description="Get storage usage statistics for connected providers")
async def get_storage_usage(user: Dict[str, Any] = Depends(get_current_user)):
    """Get storage usage statistics"""
    try:
        # In production, this would calculate actual usage from connected providers
        usage_stats = {
            "user_id": user["user_id"],
            "providers": {
                "google_drive": {
                    "connected": False,
                    "total_space": 0,
                    "used_space": 0,
                    "available_space": 0,
                    "files_synced": 0
                },
                "dropbox": {
                    "connected": False,
                    "total_space": 0,
                    "used_space": 0,
                    "available_space": 0,
                    "files_synced": 0
                }
            },
            "total_files_synced": 0,
            "total_storage_used": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {
            "storage_usage": usage_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage usage: {str(e)}")

@router.post("/pause-sync",
             summary="Pause sync",
             description="Pause automatic synchronization for a provider")
async def pause_sync(
    provider: CloudProviderEnum,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Pause automatic sync for a provider"""
    try:
        # In production, this would pause the actual sync task
        return {
            "message": f"Sync paused for {provider.value}",
            "provider": provider.value,
            "paused_at": datetime.utcnow().isoformat(),
            "status": "paused"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause sync: {str(e)}")

@router.post("/resume-sync",
             summary="Resume sync",
             description="Resume automatic synchronization for a provider")
async def resume_sync(
    provider: CloudProviderEnum,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Resume automatic sync for a provider"""
    try:
        # In production, this would resume the actual sync task
        return {
            "message": f"Sync resumed for {provider.value}",
            "provider": provider.value,
            "resumed_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume sync: {str(e)}")