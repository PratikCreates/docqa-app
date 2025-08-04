"""
API middleware for rate limiting, authentication, and request tracking
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from services.rate_limiter import rate_limiter
from services.auth_service import auth_service
from datetime import datetime
import time
import uuid
import json

class APIMiddleware(BaseHTTPMiddleware):
    """Comprehensive API middleware for authentication, rate limiting, and tracking"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/register",
            "/auth/login",
            "/supported-formats",
            "/models",
            "/question-categories"
        }
        
        # Endpoints that don't require rate limiting
        self.rate_limit_exempt = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through middleware pipeline"""
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        try:
            # Add CORS headers for all requests
            response = await self._add_cors_headers(request, call_next)
            
            # Skip middleware for OPTIONS requests
            if request.method == "OPTIONS":
                return response
            
            # Skip middleware for public endpoints
            if self._is_public_endpoint(request.url.path):
                return await self._finalize_response(request, response, start_time)
            
            # Authenticate request
            user_info = await self._authenticate_request(request)
            if not user_info:
                return self._create_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Authentication required",
                    "AUTHENTICATION_REQUIRED",
                    request_id
                )
            
            request.state.user = user_info
            
            # Apply rate limiting
            if not self._is_rate_limit_exempt(request.url.path):
                rate_limit_result = await self._apply_rate_limiting(request, user_info)
                if not rate_limit_result["allowed"]:
                    return self._create_rate_limit_response(rate_limit_result, request_id)
            
            # Process request
            response = await call_next(request)
            
            # Add API headers
            response = await self._add_api_headers(request, response, user_info)
            
            return await self._finalize_response(request, response, start_time)
            
        except HTTPException as e:
            return self._create_error_response(
                e.status_code,
                e.detail,
                "HTTP_EXCEPTION",
                request_id
            )
        except Exception as e:
            print(f"Middleware error: {str(e)}")
            return self._create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal server error",
                "INTERNAL_ERROR",
                request_id
            )
    
    async def _add_cors_headers(self, request: Request, call_next):
        """Add CORS headers to response"""
        
        response = await call_next(request)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key, X-Request-ID"
        response.headers["Access-Control-Expose-Headers"] = "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-Request-ID"
        
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require authentication)"""
        
        # Exact match
        if path in self.public_endpoints:
            return True
        
        # Pattern matching for dynamic routes
        public_patterns = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static/"
        ]
        
        return any(path.startswith(pattern) for pattern in public_patterns)
    
    def _is_rate_limit_exempt(self, path: str) -> bool:
        """Check if endpoint is exempt from rate limiting"""
        return path in self.rate_limit_exempt
    
    async def _authenticate_request(self, request: Request) -> dict:
        """Authenticate the request using JWT or API key"""
        
        # Try JWT authentication first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = auth_service.verify_token(token)
            if payload:
                return {
                    "user_id": payload["user_id"],
                    "email": payload["email"],
                    "auth_type": "jwt",
                    "token_type": payload.get("type", "access")
                }
        
        # Try API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user_info = await self._verify_api_key(api_key)
            if user_info:
                return {
                    **user_info,
                    "auth_type": "api_key"
                }
        
        return None
    
    async def _verify_api_key(self, api_key: str) -> dict:
        """Verify API key and return user information"""
        
        try:
            # In production, this would check against a database
            # For now, we'll use a simple cache-based approach
            from services.cache_service import cache_service
            
            user_info = cache_service.get(f"api_key:{api_key}")
            if user_info:
                return user_info
            
            # If not in cache, this would typically query the database
            # For demo purposes, we'll return None
            return None
            
        except Exception as e:
            print(f"API key verification error: {str(e)}")
            return None
    
    async def _apply_rate_limiting(self, request: Request, user_info: dict) -> dict:
        """Apply rate limiting to the request"""
        
        user_id = user_info["user_id"]
        endpoint = request.url.path
        user_tier = rate_limiter.get_user_tier(user_id)
        
        is_allowed, rate_info = rate_limiter.check_rate_limit(user_id, endpoint, user_tier)
        
        return rate_info
    
    async def _add_api_headers(self, request: Request, response: Response, user_info: dict) -> Response:
        """Add API-specific headers to response"""
        
        # Add request ID
        response.headers["X-Request-ID"] = request.state.request_id
        
        # Add rate limit headers if rate limiting was applied
        if hasattr(request.state, 'rate_limit_info'):
            rate_info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
            response.headers["X-RateLimit-Window"] = rate_info["window"]
        
        # Add API version
        response.headers["X-API-Version"] = "2.0.0"
        
        # Add processing time
        if hasattr(request.state, 'start_time'):
            processing_time = time.time() - request.state.start_time
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
        
        return response
    
    async def _finalize_response(self, request: Request, response: Response, start_time: float) -> Response:
        """Finalize response with logging and metrics"""
        
        processing_time = time.time() - start_time
        
        # Log request (in production, use proper logging)
        log_data = {
            "request_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time": processing_time,
            "user_id": getattr(request.state, 'user', {}).get('user_id'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"API Request: {json.dumps(log_data)}")
        
        return response
    
    def _create_error_response(self, status_code: int, detail: str, error_code: str, request_id: str) -> JSONResponse:
        """Create standardized error response"""
        
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            },
            headers={
                "X-Request-ID": request_id,
                "X-API-Version": "2.0.0"
            }
        )
    
    def _create_rate_limit_response(self, rate_info: dict, request_id: str) -> JSONResponse:
        """Create rate limit exceeded response"""
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded. Limit: {rate_info['limit']} requests per {rate_info['window']}",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "rate_limit": {
                    "limit": rate_info["limit"],
                    "remaining": rate_info["remaining"],
                    "reset_time": rate_info["reset_time"],
                    "window": rate_info["window"],
                    "user_tier": rate_info["user_tier"]
                }
            },
            headers={
                "X-Request-ID": request_id,
                "X-API-Version": "2.0.0",
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset_time"]),
                "Retry-After": str(max(1, rate_info["reset_time"] - int(time.time())))
            }
        )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request logging and metrics"""
    
    async def dispatch(self, request: Request, call_next):
        """Log request details and metrics"""
        
        start_time = time.time()
        
        # Log incoming request
        print(f"Incoming request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        processing_time = time.time() - start_time
        print(f"Response: {response.status_code} ({processing_time:.3f}s)")
        
        return response