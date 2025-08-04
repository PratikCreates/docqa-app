"""
Redis caching service for session management and performance optimization
"""

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available - caching will be disabled")

import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import os

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        if not REDIS_AVAILABLE:
            self.redis_client = None
            return
            
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection established")
        except (redis.ConnectionError, Exception) as e:
            print(f"❌ Redis connection failed - caching will be disabled: {str(e)}")
            self.redis_client = None
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle for complex objects
            return pickle.loads(value)
    
    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Set a value in cache with optional expiration"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = self._serialize_value(value)
            if expire_seconds:
                return self.redis_client.setex(key, expire_seconds, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
        except Exception as e:
            print(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            print(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            print(f"Cache expire error for key {key}: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            print(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    def set_hash(self, key: str, field: str, value: Any) -> bool:
        """Set a field in a hash"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = self._serialize_value(value)
            return bool(self.redis_client.hset(key, field, serialized_value))
        except Exception as e:
            print(f"Cache hash set error for key {key}, field {field}: {str(e)}")
            return False
    
    def get_hash(self, key: str, field: str) -> Optional[Any]:
        """Get a field from a hash"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.hget(key, field)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            print(f"Cache hash get error for key {key}, field {field}: {str(e)}")
            return None
    
    def get_all_hash(self, key: str) -> Dict[str, Any]:
        """Get all fields from a hash"""
        if not self.redis_client:
            return {}
        
        try:
            hash_data = self.redis_client.hgetall(key)
            result = {}
            for field, value in hash_data.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                result[field_str] = self._deserialize_value(value)
            return result
        except Exception as e:
            print(f"Cache hash get all error for key {key}: {str(e)}")
            return {}
    
    def delete_hash_field(self, key: str, field: str) -> bool:
        """Delete a field from a hash"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.hdel(key, field))
        except Exception as e:
            print(f"Cache hash delete error for key {key}, field {field}: {str(e)}")
            return False
    
    def add_to_set(self, key: str, *values: Any) -> int:
        """Add values to a set"""
        if not self.redis_client:
            return 0
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            return self.redis_client.sadd(key, *serialized_values)
        except Exception as e:
            print(f"Cache set add error for key {key}: {str(e)}")
            return 0
    
    def get_set_members(self, key: str) -> List[Any]:
        """Get all members of a set"""
        if not self.redis_client:
            return []
        
        try:
            members = self.redis_client.smembers(key)
            return [self._deserialize_value(member) for member in members]
        except Exception as e:
            print(f"Cache set members error for key {key}: {str(e)}")
            return []
    
    def remove_from_set(self, key: str, *values: Any) -> int:
        """Remove values from a set"""
        if not self.redis_client:
            return 0
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            return self.redis_client.srem(key, *serialized_values)
        except Exception as e:
            print(f"Cache set remove error for key {key}: {str(e)}")
            return 0
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error for pattern {pattern}: {str(e)}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information and statistics"""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Session management helpers
class SessionManager:
    """Session management using Redis cache"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.session_prefix = "session:"
        self.default_expire = 3600  # 1 hour
    
    def create_session(self, user_id: str, session_data: Dict[str, Any], expire_seconds: Optional[int] = None) -> str:
        """Create a new session"""
        import uuid
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data["user_id"] = user_id
        session_data["created_at"] = str(datetime.now())
        
        expire_time = expire_seconds or self.default_expire
        self.cache.set(session_key, session_data, expire_time)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"
        return self.cache.get(session_key)
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"{self.session_prefix}{session_id}"
        existing_session = self.cache.get(session_key)
        
        if existing_session:
            existing_session.update(session_data)
            return self.cache.set(session_key, existing_session, self.default_expire)
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.session_prefix}{session_id}"
        return self.cache.delete(session_key)
    
    def extend_session(self, session_id: str, expire_seconds: Optional[int] = None) -> bool:
        """Extend session expiration"""
        session_key = f"{self.session_prefix}{session_id}"
        expire_time = expire_seconds or self.default_expire
        return self.cache.expire(session_key, expire_time)

# Global cache service instance
cache_service = CacheService()
session_manager = SessionManager(cache_service)