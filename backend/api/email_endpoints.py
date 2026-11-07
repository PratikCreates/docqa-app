"""
Email Integration API Endpoints
Provides REST API for email configuration, monitoring, and document sharing
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.email_service import email_service
from api.auth_middleware import api_middleware

router = APIRouter(prefix="/email", tags=["Email Integration"])

class EmailConfigRequest(BaseModel):
    """Request model for email configuration"""
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    username: EmailStr
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    
    @validator('smtp_port', 'imap_port')
    def validate_ports(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

class DocumentShareRequest(BaseModel):
    """Request model for sharing documents via email"""
    recipient_email: EmailStr
    document_id: str
    document_name: str
    share_message: Optional[str] = None

class EmailUploadRequest(BaseModel):
    """Request model for processing email uploads"""
    sender_email: EmailStr
    subject: str
    body: str
    attachments: Optional[List[Dict[str, Any]]] = None

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

@router.post("/configure",
             summary="Configure email settings",
             description="Configure SMTP/IMAP settings for email integration")
async def configure_email(
    config: EmailConfigRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Configure email settings for the user"""
    try:
        result = await email_service.configure_email(
            user_id=user["user_id"],
            email_config=config.dict()
        )
        
        return {
            "message": "Email configuration saved successfully",
            "configuration": {
                "smtp_server": config.smtp_server,
                "smtp_port": config.smtp_port,
                "imap_server": config.imap_server,
                "imap_port": config.imap_port,
                "username": config.username,
                "use_tls": config.use_tls,
                "use_ssl": config.use_ssl
            },
            "test_result": result["test_result"],
            "configured_at": result["configured_at"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure email: {str(e)}")

@router.get("/configuration",
            summary="Get email configuration",
            description="Get current email configuration (without sensitive data)")
async def get_email_configuration(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current email configuration"""
    try:
        config = await email_service._get_user_email_config(user["user_id"])
        
        if not config:
            raise HTTPException(status_code=404, detail="Email not configured")
        
        # Return configuration without password
        safe_config = {
            "smtp_server": config["smtp_server"],
            "smtp_port": config["smtp_port"],
            "imap_server": config["imap_server"],
            "imap_port": config["imap_port"],
            "username": config["username"],
            "use_tls": config.get("use_tls", True),
            "use_ssl": config.get("use_ssl", False),
            "configured": True
        }
        
        return {
            "configuration": safe_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@router.post("/monitoring/start",
             summary="Start email monitoring",
             description="Start monitoring email for document uploads")
async def start_email_monitoring(user: Dict[str, Any] = Depends(get_current_user)):
    """Start email monitoring for document uploads"""
    try:
        result = await email_service.start_email_monitoring(user["user_id"])
        
        return {
            "message": "Email monitoring started successfully",
            "user_id": user["user_id"],
            "started_at": result["started_at"],
            "instructions": {
                "upload_documents": "Send emails with document attachments to your configured email",
                "processing_tags": "Use #tags: tag1, tag2 in email body to add tags",
                "processing_instructions": "Use #process: instruction in email body for custom processing",
                "supported_formats": ["PDF", "DOCX", "TXT", "MD", "HTML", "Images"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/monitoring/stop",
             summary="Stop email monitoring",
             description="Stop monitoring email for document uploads")
async def stop_email_monitoring(user: Dict[str, Any] = Depends(get_current_user)):
    """Stop email monitoring"""
    try:
        # Remove monitoring flag
        monitoring_key = f"email_monitoring:{user['user_id']}"
        email_service.cache.delete(monitoring_key)
        
        return {
            "message": "Email monitoring stopped",
            "user_id": user["user_id"],
            "stopped_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/monitoring/status",
            summary="Get monitoring status",
            description="Get current email monitoring status")
async def get_monitoring_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get email monitoring status"""
    try:
        monitoring_key = f"email_monitoring:{user['user_id']}"
        is_monitoring = email_service.cache.get(monitoring_key) or False
        
        return {
            "is_monitoring": bool(is_monitoring),
            "user_id": user["user_id"],
            "last_check": email_service.last_check.isoformat() if hasattr(email_service, 'last_check') else None,
            "monitoring_interval": "5 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")

@router.post("/upload",
             summary="Process email upload",
             description="Process an email for document uploads")
async def process_email_upload(
    email_file: UploadFile = File(..., description="Raw email file (.eml format)"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Process email file for document uploads"""
    try:
        # Read email content
        email_content = await email_file.read()
        
        # Validate file size (max 10MB)
        if len(email_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Email file too large (max 10MB)")
        
        # Process email
        result = await email_service.process_email_upload(
            user_id=user["user_id"],
            raw_email=email_content
        )
        
        return {
            "message": "Email processed successfully",
            "processing_result": result,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process email: {str(e)}")

@router.post("/share",
             summary="Share document via email",
             description="Send an email to share a document with someone")
async def share_document_via_email(
    share_request: DocumentShareRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Share a document via email"""
    try:
        result = await email_service.send_document_share_email(
            sender_user_id=user["user_id"],
            recipient_email=share_request.recipient_email,
            document_id=share_request.document_id,
            document_name=share_request.document_name,
            share_message=share_request.share_message
        )
        
        return {
            "message": "Document shared successfully via email",
            "share_details": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share document: {str(e)}")

@router.post("/test-connection",
             summary="Test email connection",
             description="Test SMTP/IMAP connection with provided settings")
async def test_email_connection(
    config: EmailConfigRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Test email server connection"""
    try:
        test_result = await email_service._test_email_connection(config.dict())
        
        return {
            "connection_test": test_result,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/send-notification",
             summary="Send processing notification",
             description="Send email notification about document processing")
async def send_processing_notification(
    document_name: str,
    status: str,
    results: Optional[Dict[str, Any]] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Send processing notification email"""
    try:
        success = await email_service.send_processing_notification(
            user_id=user["user_id"],
            document_name=document_name,
            status=status,
            results=results or {}
        )
        
        if success:
            return {
                "message": "Notification email sent successfully",
                "document_name": document_name,
                "status": status,
                "sent_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification email")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.get("/supported-formats",
            summary="Get supported email formats",
            description="Get list of supported document formats for email uploads")
async def get_supported_formats():
    """Get supported document formats for email uploads"""
    return {
        "supported_formats": {
            "documents": [
                {"type": "PDF", "mime_type": "application/pdf", "extensions": [".pdf"]},
                {"type": "Word Document", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "extensions": [".docx"]},
                {"type": "Plain Text", "mime_type": "text/plain", "extensions": [".txt"]},
                {"type": "Markdown", "mime_type": "text/markdown", "extensions": [".md"]},
                {"type": "HTML", "mime_type": "text/html", "extensions": [".html", ".htm"]}
            ],
            "images": [
                {"type": "JPEG", "mime_type": "image/jpeg", "extensions": [".jpg", ".jpeg"]},
                {"type": "PNG", "mime_type": "image/png", "extensions": [".png"]},
                {"type": "GIF", "mime_type": "image/gif", "extensions": [".gif"]},
                {"type": "BMP", "mime_type": "image/bmp", "extensions": [".bmp"]},
                {"type": "TIFF", "mime_type": "image/tiff", "extensions": [".tiff", ".tif"]}
            ],
            "code": [
                {"type": "Python", "mime_type": "text/x-python", "extensions": [".py"]},
                {"type": "JavaScript", "mime_type": "text/javascript", "extensions": [".js"]},
                {"type": "TypeScript", "mime_type": "text/typescript", "extensions": [".ts"]},
                {"type": "Java", "mime_type": "text/x-java-source", "extensions": [".java"]},
                {"type": "C++", "mime_type": "text/x-c++src", "extensions": [".cpp", ".cc"]},
                {"type": "C", "mime_type": "text/x-csrc", "extensions": [".c"]},
                {"type": "Shell Script", "mime_type": "text/x-shellscript", "extensions": [".sh"]}
            ]
        },
        "email_instructions": {
            "tags": "Add #tags: tag1, tag2 in email body to tag documents",
            "processing": "Add #process: instruction in email body for custom processing",
            "questions": "Add #questions: 5 to generate specific number of questions",
            "model": "Add #model: model-name to use specific AI model",
            "sharing": "Add #share: email@example.com to share processed document"
        },
        "limits": {
            "max_attachment_size": "10MB per attachment",
            "max_email_size": "25MB total",
            "max_attachments": 10,
            "supported_email_formats": [".eml", ".msg"]
        }
    }

@router.delete("/configuration",
               summary="Delete email configuration",
               description="Remove email configuration and stop monitoring")
async def delete_email_configuration(user: Dict[str, Any] = Depends(get_current_user)):
    """Delete email configuration"""
    try:
        # Remove configuration
        config_key = f"email_config:{user['user_id']}"
        email_service.cache.delete(config_key)
        
        # Stop monitoring
        monitoring_key = f"email_monitoring:{user['user_id']}"
        email_service.cache.delete(monitoring_key)
        
        return {
            "message": "Email configuration deleted successfully",
            "user_id": user["user_id"],
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")

@router.get("/stats",
            summary="Get email integration statistics",
            description="Get statistics about email processing and uploads")
async def get_email_stats(user: Dict[str, Any] = Depends(get_current_user)):
    """Get email integration statistics"""
    try:
        # In production, this would query actual statistics from database
        stats = {
            "total_emails_processed": 0,
            "documents_uploaded_via_email": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "average_processing_time": 0,
            "most_common_formats": [],
            "last_email_processed": None,
            "monitoring_status": {
                "is_active": bool(email_service.cache.get(f"email_monitoring:{user['user_id']}")),
                "last_check": email_service.last_check.isoformat() if hasattr(email_service, 'last_check') else None
            }
        }
        
        return {
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")