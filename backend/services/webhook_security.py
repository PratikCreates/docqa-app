"""
Webhook Security and Validation Utilities
Provides security features for webhook endpoints including signature verification,
rate limiting, and payload validation
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlparse
import re

@dataclass
class WebhookSecurityConfig:
    """Webhook security configuration"""
    max_payload_size: int = 1024 * 1024  # 1MB
    signature_tolerance: int = 300  # 5 minutes
    allowed_schemes: List[str] = None
    blocked_domains: List[str] = None
    required_headers: List[str] = None
    
    def __post_init__(self):
        if self.allowed_schemes is None:
            self.allowed_schemes = ["https"]  # Only HTTPS by default
        if self.blocked_domains is None:
            self.blocked_domains = ["localhost", "127.0.0.1", "0.0.0.0"]
        if self.required_headers is None:
            self.required_headers = ["X-Webhook-Signature"]

class WebhookSecurityValidator:
    """Comprehensive webhook security validation"""
    
    def __init__(self, config: Optional[WebhookSecurityConfig] = None):
        """Initialize webhook security validator"""
        self.config = config or WebhookSecurityConfig()
        
        # Common malicious patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:text/html',  # Data URLs
            r'vbscript:',  # VBScript
            r'on\w+\s*=',  # Event handlers
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
    
    def validate_webhook_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate webhook URL for security
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in self.config.allowed_schemes:
                return False, f"Scheme '{parsed.scheme}' not allowed. Allowed schemes: {self.config.allowed_schemes}"
            
            # Check for blocked domains
            hostname = parsed.hostname
            if hostname in self.config.blocked_domains:
                return False, f"Domain '{hostname}' is blocked"
            
            # Check for private/internal IP ranges
            if self._is_private_ip(hostname):
                return False, "Private IP addresses are not allowed"
            
            # Check for suspicious patterns in URL
            if self._contains_malicious_patterns(url):
                return False, "URL contains potentially malicious content"
            
            # Check URL length
            if len(url) > 2048:
                return False, "URL too long (max 2048 characters)"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"
    
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate webhook payload for security
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check payload size
            payload_str = json.dumps(payload)
            if len(payload_str.encode('utf-8')) > self.config.max_payload_size:
                return False, f"Payload too large (max {self.config.max_payload_size} bytes)"
            
            # Check for malicious content
            if self._contains_malicious_patterns(payload_str):
                return False, "Payload contains potentially malicious content"
            
            # Validate payload structure
            if not self._validate_payload_structure(payload):
                return False, "Invalid payload structure"
            
            return True, None
            
        except Exception as e:
            return False, f"Payload validation error: {str(e)}"
    
    def verify_signature(self, payload: Dict[str, Any], signature: str, 
                        secret: str, timestamp: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Verify webhook signature
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check timestamp if provided
            if timestamp:
                try:
                    ts = int(timestamp)
                    current_time = int(time.time())
                    if abs(current_time - ts) > self.config.signature_tolerance:
                        return False, "Timestamp outside tolerance window"
                except ValueError:
                    return False, "Invalid timestamp format"
            
            # Create expected signature
            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = self._create_signature(secret, payload_str, timestamp)
            
            # Compare signatures (constant time comparison)
            if not self._constant_time_compare(signature, expected_signature):
                return False, "Invalid signature"
            
            return True, None
            
        except Exception as e:
            return False, f"Signature verification error: {str(e)}"
    
    def sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize payload by removing potentially dangerous content"""
        return self._sanitize_recursive(payload)
    
    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP address"""
        if not hostname:
            return False
        
        try:
            import ipaddress
            ip = ipaddress.ip_address(hostname)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # Not an IP address, check for localhost patterns
            localhost_patterns = [
                'localhost',
                '127.0.0.1',
                '0.0.0.0',
                '::1',
                'local',
                '.local'
            ]
            return any(pattern in hostname.lower() for pattern in localhost_patterns)
    
    def _contains_malicious_patterns(self, content: str) -> bool:
        """Check if content contains malicious patterns"""
        return any(pattern.search(content) for pattern in self.compiled_patterns)
    
    def _validate_payload_structure(self, payload: Dict[str, Any]) -> bool:
        """Validate basic payload structure"""
        # Check for required fields
        required_fields = ["event", "timestamp", "data"]
        for field in required_fields:
            if field not in payload:
                return False
        
        # Check field types
        if not isinstance(payload.get("event"), str):
            return False
        
        if not isinstance(payload.get("timestamp"), str):
            return False
        
        if not isinstance(payload.get("data"), dict):
            return False
        
        return True
    
    def _create_signature(self, secret: str, payload: str, timestamp: Optional[str] = None) -> str:
        """Create HMAC signature for payload"""
        # Include timestamp in signature if provided
        message = f"{timestamp}.{payload}" if timestamp else payload
        
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def _sanitize_recursive(self, obj: Any) -> Any:
        """Recursively sanitize object"""
        if isinstance(obj, dict):
            return {k: self._sanitize_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._sanitize_string(obj)
        else:
            return obj
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content"""
        # Remove malicious patterns
        sanitized = text
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Limit string length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "..."
        
        return sanitized

class WebhookRateLimiter:
    """Rate limiter specifically for webhook deliveries"""
    
    def __init__(self):
        """Initialize webhook rate limiter"""
        self.delivery_history: Dict[str, List[datetime]] = {}
        self.limits = {
            "per_minute": 60,
            "per_hour": 1000,
            "burst": 10
        }
    
    def check_delivery_rate_limit(self, webhook_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if webhook delivery is within rate limits
        
        Returns:
            Tuple of (is_allowed, rate_info)
        """
        now = datetime.utcnow()
        
        # Initialize history if not exists
        if webhook_id not in self.delivery_history:
            self.delivery_history[webhook_id] = []
        
        history = self.delivery_history[webhook_id]
        
        # Clean old entries
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Remove old entries
        history[:] = [ts for ts in history if ts > hour_ago]
        
        # Count recent deliveries
        minute_count = sum(1 for ts in history if ts > minute_ago)
        hour_count = len(history)
        
        # Check limits
        if minute_count >= self.limits["per_minute"]:
            return False, {
                "limit_exceeded": "per_minute",
                "limit": self.limits["per_minute"],
                "current": minute_count,
                "reset_time": (minute_ago + timedelta(minutes=1)).isoformat()
            }
        
        if hour_count >= self.limits["per_hour"]:
            return False, {
                "limit_exceeded": "per_hour",
                "limit": self.limits["per_hour"],
                "current": hour_count,
                "reset_time": (hour_ago + timedelta(hours=1)).isoformat()
            }
        
        # Check burst limit (last 10 seconds)
        burst_ago = now - timedelta(seconds=10)
        burst_count = sum(1 for ts in history if ts > burst_ago)
        
        if burst_count >= self.limits["burst"]:
            return False, {
                "limit_exceeded": "burst",
                "limit": self.limits["burst"],
                "current": burst_count,
                "reset_time": (burst_ago + timedelta(seconds=10)).isoformat()
            }
        
        # Record this delivery
        history.append(now)
        
        return True, {
            "limit_exceeded": None,
            "minute_remaining": self.limits["per_minute"] - minute_count - 1,
            "hour_remaining": self.limits["per_hour"] - hour_count - 1,
            "burst_remaining": self.limits["burst"] - burst_count - 1
        }

class WebhookEventFilter:
    """Filter and validate webhook events"""
    
    def __init__(self):
        """Initialize event filter"""
        self.event_schemas = {
            "document.uploaded": {
                "required": ["document_id", "filename", "user_id"],
                "optional": ["file_size", "content_type", "tags"]
            },
            "document.processed": {
                "required": ["document_id", "processing_time", "status"],
                "optional": ["extracted_text_length", "confidence_score"]
            },
            "search.completed": {
                "required": ["query", "results_count", "search_time"],
                "optional": ["search_type", "filters"]
            }
        }
    
    def validate_event(self, event_type: str, event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate event data against schema
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if event_type not in self.event_schemas:
            return True, None  # Allow unknown events
        
        schema = self.event_schemas[event_type]
        
        # Check required fields
        for field in schema["required"]:
            if field not in event_data:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    def filter_sensitive_data(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from event payload"""
        sensitive_fields = [
            "password", "secret", "token", "key", "api_key",
            "private_key", "auth", "credential", "session"
        ]
        
        filtered_data = {}
        for key, value in event_data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                filtered_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered_data[key] = self.filter_sensitive_data(event_type, value)
            else:
                filtered_data[key] = value
        
        return filtered_data

# Global instances
webhook_security = WebhookSecurityValidator()
webhook_rate_limiter = WebhookRateLimiter()
webhook_event_filter = WebhookEventFilter()