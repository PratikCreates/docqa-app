"""
API Authentication and Rate Limiting Middleware
Implements JWT authentication, API key validation, and rate limiting
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import jwt
import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import secrets

class AuthMethod(Enum):
    """Authentication methods"""
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    BEARER_TOKEN = "bearer_token"

class RateLimitTier(Enum):
    """Rate limit tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests_per_hour: int
    requests_per_minute: int
    burst_limit: int

@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    tier: RateLimitTier
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    permissions: list

@dataclass
class AuthResult:
    """Authentication result"""
    is_authenticated: bool
    user_id: Optional[str]
    auth_method: Optional[AuthMethod]
    tier: Optional[RateLimitTier]
    permissions: list
    error_message: Optional[str]

class APIAuthenticationService:
    """API authentication and authorization service"""
    
    def __init__(self):
        """Initialize the authentication service"""
        self.jwt_secret = "your-secret-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        # Rate limit configurations
        self.rate_limits = {
            RateLimitTier.FREE: RateLimit(100, 10, 20),
            RateLimitTier.PRO: RateLimit(1000, 50, 100),
            RateLimitTier.ENTERPRISE: RateLimit(10000, 500, 1000)
        }
        
        # In-memory storage (in production, use Redis or database)
        self.api_keys: Dict[str, APIKey] = {}
        self.rate_limit_data: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Initialize with some demo API keys
        self._create_demo_api_keys()
        
        print("[AUTH] API Authentication Service initialized")
    
    def create_api_key(self, user_id: str, name: str, tier: RateLimitTier = RateLimitTier.FREE,
                      permissions: Optional[list] = None) -> Tuple[str, str]:
        """
        Create a new API key for a user
        
        Returns:
            Tuple of (api_key, key_id)
        """
        if permissions is None:
            permissions = ["read", "write"]
        
        # Generate API key
        api_key = f"docai_{secrets.token_urlsafe(32)}"
        key_id = secrets.token_urlsafe(16)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store API key info
        self.api_keys[api_key] = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            tier=tier,
            created_at=datetime.utcnow(),
            last_used=None,
            is_active=True,
            permissions=permissions
        )
        
        return api_key, key_id
    
    def validate_api_key(self, api_key: str) -> AuthResult:
        """Validate an API key"""
        if not api_key or api_key not in self.api_keys:
            return AuthResult(
                is_authenticated=False,
                user_id=None,
                auth_method=None,
                tier=None,
                permissions=[],
                error_message="Invalid API key"
            )
        
        key_info = self.api_keys[api_key]
        
        if not key_info.is_active:
            return AuthResult(
                is_authenticated=False,
                user_id=None,
                auth_method=None,
                tier=None,
                permissions=[],
                error_message="API key is inactive"
            )
        
        # Update last used timestamp
        key_info.last_used = datetime.utcnow()
        
        return AuthResult(
            is_authenticated=True,
            user_id=key_info.user_id,
            auth_method=AuthMethod.API_KEY,
            tier=key_info.tier,
            permissions=key_info.permissions,
            error_message=None
        )
    
    def create_jwt_token(self, user_id: str, user_email: str, 
                        permissions: Optional[list] = None) -> str:
        """Create a JWT token for a user"""
        if permissions is None:
            permissions = ["read", "write"]
        
        payload = {
            "user_id": user_id,
            "email": user_email,
            "permissions": permissions,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def validate_jwt_token(self, token: str) -> AuthResult:
        """Validate a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            return AuthResult(
                is_authenticated=True,
                user_id=payload.get("user_id"),
                auth_method=AuthMethod.JWT_TOKEN,
                tier=RateLimitTier.PRO,  # Default tier for JWT users
                permissions=payload.get("permissions", []),
                error_message=None
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                is_authenticated=False,
                user_id=None,
                auth_method=None,
                tier=None,
                permissions=[],
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError:
            return AuthResult(
                is_authenticated=False,
                user_id=None,
                auth_method=None,
                tier=None,
                permissions=[],
                error_message="Invalid token"
            )
    
    def authenticate_request(self, headers: Dict[str, str]) -> AuthResult:
        """
        Authenticate a request based on headers
        
        Supports:
        - X-API-Key header for API key authentication
        - Authorization: Bearer <token> for JWT authentication
        """
        # Check for API key
        api_key = headers.get("X-API-Key") or headers.get("x-api-key")
        if api_key:
            return self.validate_api_key(api_key)
        
        # Check for Bearer token
        auth_header = headers.get("Authorization") or headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            return self.validate_jwt_token(token)
        
        return AuthResult(
            is_authenticated=False,
            user_id=None,
            auth_method=None,
            tier=None,
            permissions=[],
            error_message="No authentication provided"
        )
    
    def check_permission(self, auth_result: AuthResult, required_permission: str) -> bool:
        """Check if the authenticated user has the required permission"""
        if not auth_result.is_authenticated:
            return False
        
        return required_permission in auth_result.permissions or "admin" in auth_result.permissions
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key].is_active = False
            return True
        return False
    
    def list_user_api_keys(self, user_id: str) -> list:
        """List all API keys for a user"""
        user_keys = []
        for api_key, key_info in self.api_keys.items():
            if key_info.user_id == user_id:
                user_keys.append({
                    "key_id": key_info.key_id,
                    "name": key_info.name,
                    "tier": key_info.tier.value,
                    "created_at": key_info.created_at.isoformat(),
                    "last_used": key_info.last_used.isoformat() if key_info.last_used else None,
                    "is_active": key_info.is_active,
                    "permissions": key_info.permissions
                })
        return user_keys
    
    def _create_demo_api_keys(self):
        """Create demo API keys for testing"""
        # Free tier demo key
        demo_key_free, _ = self.create_api_key(
            user_id="demo_user_free",
            name="Demo Free Key",
            tier=RateLimitTier.FREE,
            permissions=["read"]
        )
        
        # Pro tier demo key
        demo_key_pro, _ = self.create_api_key(
            user_id="demo_user_pro",
            name="Demo Pro Key", 
            tier=RateLimitTier.PRO,
            permissions=["read", "write"]
        )
        
        # Enterprise tier demo key
        demo_key_enterprise, _ = self.create_api_key(
            user_id="demo_user_enterprise",
            name="Demo Enterprise Key",
            tier=RateLimitTier.ENTERPRISE,
            permissions=["read", "write", "admin"]
        )
        
        print(f"[API] Demo API Keys created:")
        print(f"   Free: {demo_key_free}")
        print(f"   Pro: {demo_key_pro}")
        print(f"   Enterprise: {demo_key_enterprise}")

class RateLimitService:
    """Rate limiting service with sliding window algorithm"""
    
    def __init__(self, auth_service: APIAuthenticationService):
        """Initialize rate limiting service"""
        self.auth_service = auth_service
        self.request_history: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        print("[RATE] Rate Limiting Service initialized")
    
    def check_rate_limit(self, user_id: str, tier: RateLimitTier) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        rate_limit = self.auth_service.rate_limits[tier]
        
        # Clean old requests (older than 1 hour)
        hour_ago = now - 3600
        minute_ago = now - 60
        
        # Get user's request history
        user_history = self.request_history[user_id]
        
        # Clean old requests
        while user_history["hour"] and user_history["hour"][0] < hour_ago:
            user_history["hour"].popleft()
        
        while user_history["minute"] and user_history["minute"][0] < minute_ago:
            user_history["minute"].popleft()
        
        # Check limits
        hourly_requests = len(user_history["hour"])
        minute_requests = len(user_history["minute"])
        
        # Check if limits are exceeded
        if hourly_requests >= rate_limit.requests_per_hour:
            return False, {
                "limit_exceeded": "hourly",
                "limit": rate_limit.requests_per_hour,
                "current": hourly_requests,
                "reset_time": int(user_history["hour"][0] + 3600) if user_history["hour"] else int(now + 3600)
            }
        
        if minute_requests >= rate_limit.requests_per_minute:
            return False, {
                "limit_exceeded": "minute",
                "limit": rate_limit.requests_per_minute,
                "current": minute_requests,
                "reset_time": int(user_history["minute"][0] + 60) if user_history["minute"] else int(now + 60)
            }
        
        # Record this request
        user_history["hour"].append(now)
        user_history["minute"].append(now)
        
        # Calculate remaining requests
        remaining_hourly = rate_limit.requests_per_hour - hourly_requests - 1
        remaining_minute = rate_limit.requests_per_minute - minute_requests - 1
        
        return True, {
            "limit_exceeded": None,
            "hourly_limit": rate_limit.requests_per_hour,
            "hourly_remaining": remaining_hourly,
            "minute_limit": rate_limit.requests_per_minute,
            "minute_remaining": remaining_minute,
            "reset_time": int(now + 3600)
        }
    
    def get_rate_limit_headers(self, user_id: str, tier: RateLimitTier) -> Dict[str, str]:
        """Get rate limit headers for HTTP response"""
        _, rate_info = self.check_rate_limit(user_id, tier)
        
        return {
            "X-RateLimit-Limit": str(self.auth_service.rate_limits[tier].requests_per_hour),
            "X-RateLimit-Remaining": str(rate_info.get("hourly_remaining", 0)),
            "X-RateLimit-Reset": str(rate_info.get("reset_time", 0)),
            "X-RateLimit-Tier": tier.value
        }

class APIMiddleware:
    """Complete API middleware for authentication and rate limiting"""
    
    def __init__(self):
        """Initialize API middleware"""
        self.auth_service = APIAuthenticationService()
        self.rate_limit_service = RateLimitService(self.auth_service)
        print("[MIDDLEWARE] API Middleware initialized")
    
    def process_request(self, headers: Dict[str, str], path: str) -> Tuple[bool, Dict[str, Any], Dict[str, str]]:
        """
        Process incoming request for authentication and rate limiting
        
        Returns:
            Tuple of (is_allowed, response_data, headers)
        """
        # Skip authentication for health check and docs
        if path in ["/health", "/docs", "/openapi.json"]:
            return True, {}, {}
        
        # Authenticate request
        auth_result = self.auth_service.authenticate_request(headers)
        
        if not auth_result.is_authenticated:
            return False, {
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": auth_result.error_message,
                    "details": {
                        "required": "API key or Bearer token",
                        "provided": "none"
                    }
                }
            }, {}
        
        # Check rate limits
        is_allowed, rate_info = self.rate_limit_service.check_rate_limit(
            auth_result.user_id, auth_result.tier
        )
        
        # Get rate limit headers
        rate_headers = self.rate_limit_service.get_rate_limit_headers(
            auth_result.user_id, auth_result.tier
        )
        
        if not is_allowed:
            return False, {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded for {rate_info['limit_exceeded']} window",
                    "details": {
                        "limit": rate_info["limit"],
                        "current": rate_info["current"],
                        "reset_time": rate_info["reset_time"],
                        "tier": auth_result.tier.value
                    }
                }
            }, rate_headers
        
        # Request is allowed
        return True, {
            "user_id": auth_result.user_id,
            "auth_method": auth_result.auth_method.value,
            "tier": auth_result.tier.value,
            "permissions": auth_result.permissions
        }, rate_headers
    
    def create_user_token(self, user_id: str, email: str, permissions: Optional[list] = None) -> str:
        """Create JWT token for user"""
        return self.auth_service.create_jwt_token(user_id, email, permissions)
    
    def create_user_api_key(self, user_id: str, name: str, tier: RateLimitTier = RateLimitTier.FREE) -> Tuple[str, str]:
        """Create API key for user"""
        return self.auth_service.create_api_key(user_id, name, tier)

# Global API middleware instance
api_middleware = APIMiddleware()