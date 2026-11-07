"""
Webhook Service for Advanced Document Intelligence Platform
Handles webhook registration, management, delivery, and retry logic
"""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import aiohttp
import logging

from services.cache_service import cache_service

logger = logging.getLogger(__name__)

class WebhookEvent(Enum):
    """Webhook event types"""
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"
    QUESTION_GENERATED = "question.generated"
    SEARCH_COMPLETED = "search.completed"
    COMPARISON_COMPLETED = "comparison.completed"
    ANALYSIS_COMPLETED = "analysis.completed"
    USER_REGISTERED = "user.registered"
    API_KEY_CREATED = "api_key.created"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"

class WebhookStatus(Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DISABLED = "disabled"

@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    user_id: str
    url: str
    secret: str
    events: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_delivery: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 10
    timeout_seconds: int = 30
    retry_delays: List[int] = None  # Seconds between retries
    
    def __post_init__(self):
        if self.retry_delays is None:
            self.retry_delays = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour

@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: WebhookStatus
    created_at: datetime
    delivered_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 0
    next_retry: Optional[datetime] = None

class WebhookService:
    """Comprehensive webhook management service"""
    
    def __init__(self):
        """Initialize webhook service"""
        self.cache = cache_service
        self.webhooks: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.retry_queue: List[str] = []
        
        # Background retry processor will be started when needed
        self._retry_task = None
        
        logger.info("🪝 Webhook Service initialized")
    
    def start_retry_processor(self):
        """Start the background retry processor if not already running"""
        if self._retry_task is None or self._retry_task.done():
            try:
                self._retry_task = asyncio.create_task(self._process_retry_queue())
            except RuntimeError:
                # No event loop running, will start when needed
                pass
    
    async def register_webhook(self, user_id: str, url: str, events: List[str], 
                             secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a new webhook endpoint
        
        Args:
            user_id: User ID who owns the webhook
            url: Webhook endpoint URL
            events: List of events to subscribe to
            secret: Optional secret for signature verification
            
        Returns:
            Webhook registration details
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValueError("Invalid webhook URL")
        
        # Validate events
        valid_events = [e.value for e in WebhookEvent]
        invalid_events = [e for e in events if e not in valid_events]
        if invalid_events:
            raise ValueError(f"Invalid events: {invalid_events}")
        
        # Generate webhook ID and secret
        webhook_id = str(uuid.uuid4())
        if not secret:
            secret = self._generate_secret()
        
        # Create webhook endpoint
        webhook = WebhookEndpoint(
            id=webhook_id,
            user_id=user_id,
            url=url,
            secret=secret,
            events=events,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store webhook
        self.webhooks[webhook_id] = webhook
        await self._cache_webhook(webhook)
        
        # Test webhook connectivity
        test_result = await self._test_webhook_connectivity(webhook)
        
        logger.info(f"Webhook registered: {webhook_id} for user {user_id}")
        
        return {
            "webhook_id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "is_active": True,
            "test_result": test_result,
            "created_at": webhook.created_at.isoformat()
        }
    
    async def update_webhook(self, webhook_id: str, user_id: str, 
                           updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update webhook configuration"""
        webhook = await self._get_webhook(webhook_id)
        if not webhook or webhook.user_id != user_id:
            raise ValueError("Webhook not found or access denied")
        
        # Update allowed fields
        if "url" in updates:
            if not self._validate_url(updates["url"]):
                raise ValueError("Invalid webhook URL")
            webhook.url = updates["url"]
        
        if "events" in updates:
            valid_events = [e.value for e in WebhookEvent]
            invalid_events = [e for e in updates["events"] if e not in valid_events]
            if invalid_events:
                raise ValueError(f"Invalid events: {invalid_events}")
            webhook.events = updates["events"]
        
        if "is_active" in updates:
            webhook.is_active = bool(updates["is_active"])
        
        webhook.updated_at = datetime.utcnow()
        
        # Update storage
        self.webhooks[webhook_id] = webhook
        await self._cache_webhook(webhook)
        
        logger.info(f"Webhook updated: {webhook_id}")
        
        return {
            "webhook_id": webhook_id,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": webhook.is_active,
            "updated_at": webhook.updated_at.isoformat()
        }
    
    async def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """Delete a webhook endpoint"""
        webhook = await self._get_webhook(webhook_id)
        if not webhook or webhook.user_id != user_id:
            return False
        
        # Remove from storage
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
        
        # Remove from cache
        await self._remove_webhook_cache(webhook_id)
        
        logger.info(f"Webhook deleted: {webhook_id}")
        return True
    
    async def list_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        """List all webhooks for a user"""
        user_webhooks = []
        
        for webhook in self.webhooks.values():
            if webhook.user_id == user_id:
                user_webhooks.append({
                    "webhook_id": webhook.id,
                    "url": webhook.url,
                    "events": webhook.events,
                    "is_active": webhook.is_active,
                    "created_at": webhook.created_at.isoformat(),
                    "updated_at": webhook.updated_at.isoformat(),
                    "last_delivery": webhook.last_delivery.isoformat() if webhook.last_delivery else None,
                    "failure_count": webhook.failure_count
                })
        
        return user_webhooks
    
    async def trigger_webhook(self, event_type: str, payload: Dict[str, Any], 
                            user_id: Optional[str] = None) -> List[str]:
        """
        Trigger webhook delivery for an event
        
        Args:
            event_type: Type of event (must be valid WebhookEvent)
            payload: Event payload data
            user_id: Optional user ID to filter webhooks
            
        Returns:
            List of delivery IDs
        """
        if event_type not in [e.value for e in WebhookEvent]:
            raise ValueError(f"Invalid event type: {event_type}")
        
        # Find matching webhooks
        matching_webhooks = []
        for webhook in self.webhooks.values():
            if not webhook.is_active:
                continue
            
            if user_id and webhook.user_id != user_id:
                continue
            
            if event_type in webhook.events or "all" in webhook.events:
                matching_webhooks.append(webhook)
        
        # Create deliveries
        delivery_ids = []
        for webhook in matching_webhooks:
            delivery_id = await self._create_delivery(webhook, event_type, payload)
            delivery_ids.append(delivery_id)
        
        logger.info(f"Triggered {len(delivery_ids)} webhook deliveries for event: {event_type}")
        return delivery_ids
    
    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook delivery status"""
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            return None
        
        return {
            "delivery_id": delivery.id,
            "webhook_id": delivery.webhook_id,
            "event_type": delivery.event_type,
            "status": delivery.status.value,
            "created_at": delivery.created_at.isoformat(),
            "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
            "response_status": delivery.response_status,
            "error_message": delivery.error_message,
            "attempt_count": delivery.attempt_count,
            "next_retry": delivery.next_retry.isoformat() if delivery.next_retry else None
        }
    
    async def get_webhook_stats(self, webhook_id: str, user_id: str) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        webhook = await self._get_webhook(webhook_id)
        if not webhook or webhook.user_id != user_id:
            raise ValueError("Webhook not found or access denied")
        
        # Count deliveries by status
        stats = {
            "total_deliveries": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "pending_deliveries": 0,
            "average_response_time": 0,
            "last_24h_deliveries": 0,
            "failure_rate": 0
        }
        
        response_times = []
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        for delivery in self.deliveries.values():
            if delivery.webhook_id != webhook_id:
                continue
            
            stats["total_deliveries"] += 1
            
            if delivery.status == WebhookStatus.DELIVERED:
                stats["successful_deliveries"] += 1
                if delivery.delivered_at and delivery.created_at:
                    response_time = (delivery.delivered_at - delivery.created_at).total_seconds()
                    response_times.append(response_time)
            elif delivery.status == WebhookStatus.FAILED:
                stats["failed_deliveries"] += 1
            elif delivery.status in [WebhookStatus.PENDING, WebhookStatus.RETRYING]:
                stats["pending_deliveries"] += 1
            
            if delivery.created_at > last_24h:
                stats["last_24h_deliveries"] += 1
        
        # Calculate averages
        if response_times:
            stats["average_response_time"] = sum(response_times) / len(response_times)
        
        if stats["total_deliveries"] > 0:
            stats["failure_rate"] = stats["failed_deliveries"] / stats["total_deliveries"]
        
        return stats
    
    async def _create_delivery(self, webhook: WebhookEndpoint, event_type: str, 
                             payload: Dict[str, Any]) -> str:
        """Create a webhook delivery"""
        delivery_id = str(uuid.uuid4())
        
        # Add metadata to payload
        enhanced_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook.id,
            "delivery_id": delivery_id,
            "data": payload
        }
        
        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event_type=event_type,
            payload=enhanced_payload,
            status=WebhookStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.deliveries[delivery_id] = delivery
        
        # Attempt immediate delivery
        asyncio.create_task(self._attempt_delivery(delivery))
        
        return delivery_id
    
    async def _attempt_delivery(self, delivery: WebhookDelivery) -> bool:
        """Attempt to deliver a webhook"""
        webhook = await self._get_webhook(delivery.webhook_id)
        if not webhook or not webhook.is_active:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Webhook not found or inactive"
            return False
        
        delivery.attempt_count += 1
        delivery.status = WebhookStatus.RETRYING if delivery.attempt_count > 1 else WebhookStatus.PENDING
        
        try:
            # Create signature
            signature = self._create_signature(webhook.secret, delivery.payload)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-Delivery": delivery.id,
                "X-Webhook-Timestamp": str(int(time.time())),
                "User-Agent": "DocAI-Webhooks/2.0"
            }
            
            # Make HTTP request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=webhook.timeout_seconds)) as session:
                async with session.post(
                    webhook.url,
                    json=delivery.payload,
                    headers=headers
                ) as response:
                    delivery.response_status = response.status
                    delivery.response_body = await response.text()
                    
                    if 200 <= response.status < 300:
                        # Success
                        delivery.status = WebhookStatus.DELIVERED
                        delivery.delivered_at = datetime.utcnow()
                        webhook.last_delivery = delivery.delivered_at
                        webhook.failure_count = 0
                        
                        logger.info(f"Webhook delivered successfully: {delivery.id}")
                        return True
                    else:
                        # HTTP error
                        delivery.error_message = f"HTTP {response.status}: {delivery.response_body[:200]}"
                        
        except asyncio.TimeoutError:
            delivery.error_message = f"Timeout after {webhook.timeout_seconds} seconds"
        except Exception as e:
            delivery.error_message = str(e)
        
        # Delivery failed
        delivery.status = WebhookStatus.FAILED
        webhook.failure_count += 1
        
        # Schedule retry if not exceeded max attempts
        if delivery.attempt_count < len(webhook.retry_delays) + 1:
            retry_delay = webhook.retry_delays[min(delivery.attempt_count - 1, len(webhook.retry_delays) - 1)]
            delivery.next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
            self.retry_queue.append(delivery.id)
            
            logger.info(f"Webhook delivery failed, scheduled retry: {delivery.id} in {retry_delay}s")
        else:
            logger.error(f"Webhook delivery failed permanently: {delivery.id}")
            
            # Disable webhook if too many failures
            if webhook.failure_count >= webhook.max_failures:
                webhook.is_active = False
                logger.warning(f"Webhook disabled due to excessive failures: {webhook.id}")
        
        return False
    
    async def _process_retry_queue(self):
        """Background task to process webhook retries"""
        while True:
            try:
                current_time = datetime.utcnow()
                ready_deliveries = []
                
                # Find deliveries ready for retry
                for delivery_id in self.retry_queue[:]:
                    delivery = self.deliveries.get(delivery_id)
                    if not delivery:
                        self.retry_queue.remove(delivery_id)
                        continue
                    
                    if delivery.next_retry and delivery.next_retry <= current_time:
                        ready_deliveries.append(delivery)
                        self.retry_queue.remove(delivery_id)
                
                # Process ready deliveries
                for delivery in ready_deliveries:
                    await self._attempt_delivery(delivery)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in retry queue processor: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _test_webhook_connectivity(self, webhook: WebhookEndpoint) -> Dict[str, Any]:
        """Test webhook endpoint connectivity"""
        test_payload = {
            "event": "webhook.test",
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook.id,
            "data": {
                "message": "This is a test webhook delivery",
                "test": True
            }
        }
        
        try:
            signature = self._create_signature(webhook.secret, test_payload)
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": "webhook.test",
                "X-Webhook-Delivery": str(uuid.uuid4()),
                "User-Agent": "DocAI-Webhooks/2.0"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(webhook.url, json=test_payload, headers=headers) as response:
                    return {
                        "success": 200 <= response.status < 300,
                        "status_code": response.status,
                        "response_time": response.headers.get("X-Response-Time", "unknown"),
                        "message": "Test webhook delivered successfully" if 200 <= response.status < 300 else f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "response_time": None,
                "message": f"Connection failed: {str(e)}"
            }
    
    def _validate_url(self, url: str) -> bool:
        """Validate webhook URL"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ["http", "https"] and parsed.netloc
        except:
            return False
    
    def _generate_secret(self) -> str:
        """Generate a secure webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _create_signature(self, secret: str, payload: Dict[str, Any]) -> str:
        """Create HMAC signature for webhook payload"""
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def _get_webhook(self, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Get webhook from storage"""
        return self.webhooks.get(webhook_id)
    
    async def _cache_webhook(self, webhook: WebhookEndpoint):
        """Cache webhook data"""
        try:
            webhook_data = asdict(webhook)
            webhook_data['created_at'] = webhook.created_at.isoformat()
            webhook_data['updated_at'] = webhook.updated_at.isoformat()
            if webhook.last_delivery:
                webhook_data['last_delivery'] = webhook.last_delivery.isoformat()
            
            self.cache.set(f"webhook:{webhook.id}", webhook_data, expire_seconds=3600)
        except Exception as e:
            logger.error(f"Error caching webhook: {str(e)}")
    
    async def _remove_webhook_cache(self, webhook_id: str):
        """Remove webhook from cache"""
        try:
            self.cache.delete(f"webhook:{webhook_id}")
        except Exception as e:
            logger.error(f"Error removing webhook cache: {str(e)}")

# Global webhook service instance
webhook_service = WebhookService()