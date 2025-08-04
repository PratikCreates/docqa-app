"""
Rate limiting service for API endpoints
"""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from services.cache_service import cache_service
import hashlib

class RateLimiter:
    """Rate limiting service using Redis for distributed rate limiting"""
    
    def __init__(self):
        self.cache = cache_service
        
        # Rate limit configurations
        self.rate_limits = {
            "free": {
                "requests_per_hour": 100,
                "requests_per_minute": 10,
                "burst_limit": 5
            },
            "premium": {
                "requests_per_hour": 1000,
                "requests_per_minute": 50,
                "burst_limit": 20
            },
            "enterprise": {
                "requests_per_hour": 10000,
                "requests_per_minute": 200,
                "burst_limit": 100
            }
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/documents/upload": {"multiplier": 2.0, "description": "Document upload"},
            "/search": {"multiplier": 0.5, "description": "Search operations"},
            "/search/advanced": {"multiplier": 1.0, "description": "Advanced search"},
            "/documents/*/generate-questions": {"multiplier": 1.5, "description": "Question generation"},
            "/search/reindex": {"multiplier": 5.0, "description": "Reindexing operations"}
        }
    
    def check_rate_limit(self, user_id: str, endpoint: str, user_tier: str = "free") -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        
        if not self.cache.redis_client:
            # If Redis is not available, allow all requests
            return True, self._get_default_rate_info(user_tier)
        
        try:
            # Get rate limit configuration
            limits = self.rate_limits.get(user_tier, self.rate_limits["free"])
            
            # Apply endpoint-specific multipliers
            endpoint_config = self._get_endpoint_config(endpoint)
            multiplier = endpoint_config.get("multiplier", 1.0)
            
            adjusted_limits = {
                "requests_per_hour": int(limits["requests_per_hour"] * multiplier),
                "requests_per_minute": int(limits["requests_per_minute"] * multiplier),
                "burst_limit": int(limits["burst_limit"] * multiplier)
            }
            
            # Check different time windows
            current_time = int(time.time())
            
            # Check burst limit (last 10 seconds)
            burst_allowed, burst_info = self._check_window(
                user_id, endpoint, "burst", 10, adjusted_limits["burst_limit"], current_time
            )
            
            # Check minute limit
            minute_allowed, minute_info = self._check_window(
                user_id, endpoint, "minute", 60, adjusted_limits["requests_per_minute"], current_time
            )
            
            # Check hour limit
            hour_allowed, hour_info = self._check_window(
                user_id, endpoint, "hour", 3600, adjusted_limits["requests_per_hour"], current_time
            )
            
            # Request is allowed only if all windows allow it
            is_allowed = burst_allowed and minute_allowed and hour_allowed
            
            # Determine which limit is most restrictive
            if not burst_allowed:
                limiting_info = burst_info
                limiting_window = "burst"
            elif not minute_allowed:
                limiting_info = minute_info
                limiting_window = "minute"
            elif not hour_allowed:
                limiting_info = hour_info
                limiting_window = "hour"
            else:
                limiting_info = hour_info  # Use hour info for successful requests
                limiting_window = "hour"
            
            # If allowed, increment counters
            if is_allowed:
                self._increment_counters(user_id, endpoint, current_time)
            
            rate_info = {
                "allowed": is_allowed,
                "limit": limiting_info["limit"],
                "remaining": limiting_info["remaining"],
                "reset_time": limiting_info["reset_time"],
                "window": limiting_window,
                "user_tier": user_tier,
                "endpoint": endpoint,
                "endpoint_multiplier": multiplier
            }
            
            return is_allowed, rate_info
            
        except Exception as e:
            print(f"Rate limiting error: {str(e)}")
            # On error, allow the request but log the issue
            return True, self._get_default_rate_info(user_tier)
    
    def _check_window(self, user_id: str, endpoint: str, window: str, 
                     duration: int, limit: int, current_time: int) -> Tuple[bool, Dict]:
        """Check rate limit for a specific time window"""
        
        # Create unique key for this user, endpoint, and window
        key = f"rate_limit:{user_id}:{self._hash_endpoint(endpoint)}:{window}:{current_time // duration}"
        
        try:
            # Get current count
            current_count = self.cache.get(key) or 0
            
            # Calculate remaining and reset time
            window_start = (current_time // duration) * duration
            reset_time = window_start + duration
            remaining = max(0, limit - current_count - 1)  # -1 for the current request
            
            is_allowed = current_count < limit
            
            return is_allowed, {
                "limit": limit,
                "current": current_count,
                "remaining": remaining,
                "reset_time": reset_time,
                "window_duration": duration
            }
            
        except Exception as e:
            print(f"Error checking rate limit window {window}: {str(e)}")
            return True, {
                "limit": limit,
                "current": 0,
                "remaining": limit - 1,
                "reset_time": current_time + duration,
                "window_duration": duration
            }
    
    def _increment_counters(self, user_id: str, endpoint: str, current_time: int):
        """Increment rate limit counters for all windows"""
        
        windows = [
            ("burst", 10),
            ("minute", 60),
            ("hour", 3600)
        ]
        
        for window, duration in windows:
            key = f"rate_limit:{user_id}:{self._hash_endpoint(endpoint)}:{window}:{current_time // duration}"
            
            try:
                # Increment counter
                current_count = self.cache.increment(key, 1)
                
                # Set expiration if this is the first increment
                if current_count == 1:
                    self.cache.expire(key, duration + 10)  # Add buffer for cleanup
                    
            except Exception as e:
                print(f"Error incrementing counter for {window}: {str(e)}")
    
    def _get_endpoint_config(self, endpoint: str) -> Dict:
        """Get configuration for specific endpoint"""
        
        # Try exact match first
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Try pattern matching
        for pattern, config in self.endpoint_limits.items():
            if "*" in pattern:
                # Simple wildcard matching
                pattern_parts = pattern.split("*")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    if endpoint.startswith(prefix) and endpoint.endswith(suffix):
                        return config
        
        # Default configuration
        return {"multiplier": 1.0, "description": "Standard endpoint"}
    
    def _hash_endpoint(self, endpoint: str) -> str:
        """Create a short hash of the endpoint for cache keys"""
        return hashlib.md5(endpoint.encode()).hexdigest()[:8]
    
    def _get_default_rate_info(self, user_tier: str) -> Dict:
        """Get default rate limit info when cache is unavailable"""
        limits = self.rate_limits.get(user_tier, self.rate_limits["free"])
        
        return {
            "allowed": True,
            "limit": limits["requests_per_hour"],
            "remaining": limits["requests_per_hour"] - 1,
            "reset_time": int(time.time()) + 3600,
            "window": "hour",
            "user_tier": user_tier,
            "endpoint": "unknown",
            "endpoint_multiplier": 1.0
        }
    
    def get_user_tier(self, user_id: str) -> str:
        """Get user's rate limit tier"""
        
        try:
            # Check cache for user tier
            tier = self.cache.get(f"user_tier:{user_id}")
            if tier:
                return tier
            
            # Default to free tier
            return "free"
            
        except Exception:
            return "free"
    
    def set_user_tier(self, user_id: str, tier: str) -> bool:
        """Set user's rate limit tier"""
        
        if tier not in self.rate_limits:
            return False
        
        try:
            self.cache.set(f"user_tier:{user_id}", tier, expire_seconds=86400)  # 24 hours
            return True
        except Exception:
            return False
    
    def get_rate_limit_stats(self, user_id: str) -> Dict:
        """Get current rate limit statistics for a user"""
        
        try:
            user_tier = self.get_user_tier(user_id)
            limits = self.rate_limits[user_tier]
            current_time = int(time.time())
            
            stats = {
                "user_tier": user_tier,
                "limits": limits,
                "current_usage": {},
                "reset_times": {}
            }
            
            # Check usage for different windows
            for window, duration in [("hour", 3600), ("minute", 60), ("burst", 10)]:
                key_pattern = f"rate_limit:{user_id}:*:{window}:{current_time // duration}"
                
                # This is a simplified version - in production you'd want to
                # aggregate across all endpoints for the user
                total_usage = 0
                
                stats["current_usage"][window] = total_usage
                stats["reset_times"][window] = ((current_time // duration) + 1) * duration
            
            return stats
            
        except Exception as e:
            print(f"Error getting rate limit stats: {str(e)}")
            return {"error": "Unable to retrieve rate limit statistics"}
    
    def reset_user_limits(self, user_id: str) -> bool:
        """Reset all rate limits for a user (admin function)"""
        
        try:
            # This would require scanning and deleting all keys for the user
            # In production, you'd want a more efficient approach
            pattern = f"rate_limit:{user_id}:*"
            
            # Clear pattern would need to be implemented in cache service
            cleared = self.cache.clear_pattern(pattern)
            return cleared > 0
            
        except Exception as e:
            print(f"Error resetting user limits: {str(e)}")
            return False

# Global rate limiter instance
rate_limiter = RateLimiter()