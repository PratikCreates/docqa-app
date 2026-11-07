"""
Webhook API Endpoints for Advanced Document Intelligence Platform
Provides REST API for webhook management and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.webhook_service import webhook_service, WebhookEvent
from api.auth_middleware import api_middleware

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

class WebhookCreateRequest(BaseModel):
    """Request model for creating webhooks"""
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    
    @validator('events')
    def validate_events(cls, v):
        valid_events = [e.value for e in WebhookEvent] + ["all"]
        invalid_events = [e for e in v if e not in valid_events]
        if invalid_events:
            raise ValueError(f"Invalid events: {invalid_events}. Valid events: {valid_events}")
        return v

class WebhookUpdateRequest(BaseModel):
    """Request model for updating webhooks"""
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    
    @validator('events')
    def validate_events(cls, v):
        if v is not None:
            valid_events = [e.value for e in WebhookEvent] + ["all"]
            invalid_events = [e for e in v if e not in valid_events]
            if invalid_events:
                raise ValueError(f"Invalid events: {invalid_events}. Valid events: {valid_events}")
        return v

class WebhookTestRequest(BaseModel):
    """Request model for testing webhooks"""
    event_type: str = "webhook.test"
    test_data: Optional[Dict[str, Any]] = None

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

@router.post("/register", 
             summary="Register webhook endpoint",
             description="Register a new webhook endpoint to receive event notifications")
async def register_webhook(
    webhook_data: WebhookCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Register a new webhook endpoint"""
    try:
        result = await webhook_service.register_webhook(
            user_id=user["user_id"],
            url=str(webhook_data.url),
            events=webhook_data.events,
            secret=webhook_data.secret
        )
        
        return {
            "message": "Webhook registered successfully",
            "webhook": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")

@router.get("/", 
            summary="List webhooks",
            description="Get all webhook endpoints for the authenticated user")
async def list_webhooks(user: Dict[str, Any] = Depends(get_current_user)):
    """List all webhooks for the user"""
    try:
        webhooks = await webhook_service.list_webhooks(user["user_id"])
        
        return {
            "webhooks": webhooks,
            "total": len(webhooks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")

@router.get("/{webhook_id}",
            summary="Get webhook details",
            description="Get detailed information about a specific webhook")
async def get_webhook(
    webhook_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get webhook details"""
    try:
        webhooks = await webhook_service.list_webhooks(user["user_id"])
        webhook = next((w for w in webhooks if w["webhook_id"] == webhook_id), None)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Get webhook statistics
        stats = await webhook_service.get_webhook_stats(webhook_id, user["user_id"])
        
        return {
            "webhook": webhook,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")

@router.put("/{webhook_id}",
            summary="Update webhook",
            description="Update webhook configuration")
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update webhook configuration"""
    try:
        # Convert to dict and remove None values
        updates = {k: v for k, v in webhook_data.dict().items() if v is not None}
        
        if "url" in updates:
            updates["url"] = str(updates["url"])
        
        result = await webhook_service.update_webhook(
            webhook_id=webhook_id,
            user_id=user["user_id"],
            updates=updates
        )
        
        return {
            "message": "Webhook updated successfully",
            "webhook": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")

@router.delete("/{webhook_id}",
               summary="Delete webhook",
               description="Delete a webhook endpoint")
async def delete_webhook(
    webhook_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a webhook endpoint"""
    try:
        success = await webhook_service.delete_webhook(webhook_id, user["user_id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return {
            "message": "Webhook deleted successfully",
            "webhook_id": webhook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")

@router.post("/{webhook_id}/test",
             summary="Test webhook",
             description="Send a test event to the webhook endpoint")
async def test_webhook(
    webhook_id: str,
    test_data: WebhookTestRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Test webhook endpoint with a sample event"""
    try:
        # Verify webhook exists and belongs to user
        webhooks = await webhook_service.list_webhooks(user["user_id"])
        webhook = next((w for w in webhooks if w["webhook_id"] == webhook_id), None)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Create test payload
        test_payload = {
            "message": "This is a test webhook delivery",
            "test": True,
            "user_id": user["user_id"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if test_data.test_data:
            test_payload.update(test_data.test_data)
        
        # Trigger webhook
        delivery_ids = await webhook_service.trigger_webhook(
            event_type=test_data.event_type,
            payload=test_payload,
            user_id=user["user_id"]
        )
        
        if not delivery_ids:
            return {
                "message": "No matching webhooks found for test event",
                "event_type": test_data.event_type
            }
        
        # Get delivery status
        delivery_status = await webhook_service.get_delivery_status(delivery_ids[0])
        
        return {
            "message": "Test webhook triggered",
            "delivery_id": delivery_ids[0],
            "delivery_status": delivery_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")

@router.get("/{webhook_id}/deliveries",
            summary="Get webhook deliveries",
            description="Get delivery history for a webhook")
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get webhook delivery history"""
    try:
        # Verify webhook exists and belongs to user
        webhooks = await webhook_service.list_webhooks(user["user_id"])
        webhook = next((w for w in webhooks if w["webhook_id"] == webhook_id), None)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Get deliveries (simplified - in production would use database pagination)
        all_deliveries = []
        for delivery_id, delivery in webhook_service.deliveries.items():
            if delivery.webhook_id == webhook_id:
                delivery_info = await webhook_service.get_delivery_status(delivery_id)
                if delivery_info:
                    if not status_filter or delivery_info["status"] == status_filter:
                        all_deliveries.append(delivery_info)
        
        # Sort by creation time (newest first)
        all_deliveries.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        paginated_deliveries = all_deliveries[offset:offset + limit]
        
        return {
            "deliveries": paginated_deliveries,
            "total": len(all_deliveries),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(all_deliveries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deliveries: {str(e)}")

@router.get("/{webhook_id}/stats",
            summary="Get webhook statistics",
            description="Get detailed statistics for a webhook")
async def get_webhook_statistics(
    webhook_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed webhook statistics"""
    try:
        stats = await webhook_service.get_webhook_stats(webhook_id, user["user_id"])
        
        return {
            "webhook_id": webhook_id,
            "statistics": stats
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/events/types",
            summary="Get available event types",
            description="Get list of all available webhook event types")
async def get_event_types():
    """Get available webhook event types"""
    events = []
    for event in WebhookEvent:
        events.append({
            "name": event.value,
            "description": _get_event_description(event.value)
        })
    
    return {
        "events": events,
        "total": len(events)
    }

@router.post("/trigger",
             summary="Manual webhook trigger",
             description="Manually trigger webhooks for testing (admin only)")
async def manual_trigger_webhook(
    event_type: str,
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually trigger webhook (for testing/admin purposes)"""
    # Check if user has admin permissions
    if "admin" not in user.get("permissions", []):
        raise HTTPException(
            status_code=403, 
            detail="Admin permissions required for manual webhook triggers"
        )
    
    try:
        delivery_ids = await webhook_service.trigger_webhook(
            event_type=event_type,
            payload=payload,
            user_id=user_id
        )
        
        return {
            "message": f"Triggered {len(delivery_ids)} webhook deliveries",
            "event_type": event_type,
            "delivery_ids": delivery_ids
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger webhooks: {str(e)}")

def _get_event_description(event_type: str) -> str:
    """Get description for webhook event type"""
    descriptions = {
        "document.uploaded": "Triggered when a document is successfully uploaded",
        "document.processed": "Triggered when document processing is completed",
        "document.failed": "Triggered when document processing fails",
        "question.generated": "Triggered when questions are auto-generated for a document",
        "search.completed": "Triggered when a search operation is completed",
        "comparison.completed": "Triggered when document comparison is completed",
        "analysis.completed": "Triggered when cross-document analysis is completed",
        "user.registered": "Triggered when a new user registers",
        "api_key.created": "Triggered when a new API key is created",
        "rate_limit.exceeded": "Triggered when rate limits are exceeded"
    }
    
    return descriptions.get(event_type, "No description available")