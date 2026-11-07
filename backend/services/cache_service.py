"""
Simple cache service for the Document Intelligence Platform
"""

import json
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCacheService:
    """Simple in-memory cache service"""
    
    def __init__(self):
        self.cache = {}
        self.redis_client = None  # No Redis for now
        print("[CACHE] Cache Service initialized (in-memory)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            item = self.cache[key]
            if item['expires'] and datetime.now() > item['expires']:
                del self.cache[key]
                return None
            return item['value']
        return None
    
    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Set value in cache"""
        expires = None
        if expire_seconds:
            expires = datetime.now() + timedelta(seconds=expire_seconds)
        
        self.cache[key] = {
            'value': value,
            'expires': expires
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        current = self.get(key) or 0
        new_value = current + amount
        self.set(key, new_value)
        return new_value
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        if key in self.cache:
            self.cache[key]['expires'] = datetime.now() + timedelta(seconds=seconds)
            return True
        return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)

# Global cache service instance
cache_service = SimpleCacheService()