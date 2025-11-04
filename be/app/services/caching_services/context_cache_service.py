import redis
import pickle
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class ContextCacheService:
    """
    Service for caching and retrieving context data to improve chat agent performance.
    Uses Redis for fast access to frequently requested contexts.
    """
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Context cache service initialized with Redis")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using memory cache: {str(e)}")
            self.redis_client = None
            self._memory_cache = {}
    
    def _get_cache_key(self, cache_type: str, user_id: str, team_id: Optional[str] = None, identifier: str = None) -> str:
        """Generate cache key for context data, now with team_id support"""
        base_key = f"chat_context:{cache_type}:{user_id}"
        if team_id:
            base_key += f":team:{team_id}"
        if identifier:
            base_key += f":{identifier}"
        return base_key
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Failed to serialize data: {str(e)}")
            return pickle.dumps({"error": "serialization_failed"})
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to deserialize data: {str(e)}")
            return None
    
    def cache_learning_path_context(
        self, 
        user_id: str,
        team_id: Optional[str],
        context_data: Dict[str, Any], 
        ttl: int = 1800
    ) -> bool:
        """Cache learning path context (now team-aware)"""
        try:
            key = self._get_cache_key("learning_path", user_id, team_id)
            if self.redis_client:
                serialized_data = self._serialize_data(context_data)
                self.redis_client.setex(key, ttl, serialized_data)
            else:
                self._memory_cache[key] = {
                    'data': context_data,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
            logger.debug(f"📦 Cached learning path context for user {user_id}, team {team_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache learning path context: {str(e)}")
            return False

    def get_learning_path_context(self, user_id: str, team_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached learning path context (now team-aware)"""
        try:
            key = self._get_cache_key("learning_path", user_id, team_id)
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return self._deserialize_data(cached_data)
            else:
                if key in self._memory_cache:
                    cache_entry = self._memory_cache[key]
                    if datetime.now() < cache_entry['expires']:
                        return cache_entry['data']
                    else:
                        del self._memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve learning path context: {str(e)}")
            return None
    
    def cache_module_context(
        self, 
        user_id: str,
        module_id: int, 
        context_data: Dict[str, Any], 
        ttl: int = 1800
    ) -> bool:
        """Cache module-specific context"""
        try:
            key = self._get_cache_key("module", user_id, identifier=str(module_id))
            
            if self.redis_client:
                serialized_data = self._serialize_data(context_data)
                self.redis_client.setex(key, ttl, serialized_data)
            else:
                self._memory_cache[key] = {
                    'data': context_data,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
            
            logger.debug(f"📦 Cached module context for user {user_id}, module {module_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache module context: {str(e)}")
            return False
    
    def get_module_context(self, user_id: str, module_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached module context"""
        try:
            key = self._get_cache_key("module", user_id, identifier=str(module_id))
            
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return self._deserialize_data(cached_data)
            else:
                if key in self._memory_cache:
                    cache_entry = self._memory_cache[key]
                    if datetime.now() < cache_entry['expires']:
                        return cache_entry['data']
                    else:
                        del self._memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve module context: {str(e)}")
            return None
    
    def cache_quiz_context(
        self, 
        user_id: str,
        context_data: Dict[str, Any], 
        ttl: int = 900
    ) -> bool:
        """Cache quiz context (shorter TTL as it changes more frequently)"""
        try:
            key = self._get_cache_key("quiz", user_id)
            
            if self.redis_client:
                serialized_data = self._serialize_data(context_data)
                self.redis_client.setex(key, ttl, serialized_data)
            else:
                self._memory_cache[key] = {
                    'data': context_data,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
            
            logger.debug(f"📦 Cached quiz context for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache quiz context: {str(e)}")
            return False
    
    def get_quiz_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached quiz context"""
        try:
            key = self._get_cache_key("quiz", user_id)
            
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return self._deserialize_data(cached_data)
            else:
                if key in self._memory_cache:
                    cache_entry = self._memory_cache[key]
                    if datetime.now() < cache_entry['expires']:
                        return cache_entry['data']
                    else:
                        del self._memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve quiz context: {str(e)}")
            return None
    
    def cache_progress_context(
        self, 
        user_id: str,
        context_data: Dict[str, Any], 
        ttl: int = 600
    ) -> bool:
        """Cache progress context (shorter TTL as progress changes frequently)"""
        try:
            key = self._get_cache_key("progress", user_id)
            
            if self.redis_client:
                serialized_data = self._serialize_data(context_data)
                self.redis_client.setex(key, ttl, serialized_data)
            else:
                self._memory_cache[key] = {
                    'data': context_data,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
            
            logger.debug(f"📦 Cached progress context for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache progress context: {str(e)}")
            return False
    
    def get_progress_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached progress context"""
        try:
            key = self._get_cache_key("progress", user_id)
            
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return self._deserialize_data(cached_data)
            else:
                if key in self._memory_cache:
                    cache_entry = self._memory_cache[key]
                    if datetime.now() < cache_entry['expires']:
                        return cache_entry['data']
                    else:
                        del self._memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve progress context: {str(e)}")
            return None
    
    def invalidate_user_cache(self, user_id: str, context_types: List[str] = None) -> bool:
        """Invalidate all or specific cached contexts for a user"""
        try:
            if context_types is None:
                context_types = ["learning_path", "module", "quiz", "progress"]
            
            deleted_count = 0
            
            if self.redis_client:
                for context_type in context_types:
                    if context_type == "module":
                        # Delete all module contexts for this user
                        pattern = self._get_cache_key("module", user_id, "*")
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            deleted_count += self.redis_client.delete(*keys)
                    else:
                        key = self._get_cache_key(context_type, user_id)
                        if self.redis_client.delete(key):
                            deleted_count += 1
            else:
                # Memory cache fallback
                keys_to_delete = []
                for key in self._memory_cache.keys():
                    if f":{user_id}:" in key or key.endswith(f":{user_id}"):
                        if any(context_type in key for context_type in context_types):
                            keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    deleted_count += 1
            
            logger.info(f"🗑️ Invalidated {deleted_count} cached contexts for user {user_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                
                # Get key count by scanning for our prefixes
                key_patterns = [
                    "chat_context:learning_path:*",
                    "chat_context:module:*",
                    "chat_context:quiz:*",
                    "chat_context:progress:*"
                ]
                
                key_counts = {}
                total_keys = 0
                
                for pattern in key_patterns:
                    keys = self.redis_client.keys(pattern)
                    context_type = pattern.split(":")[1]
                    key_counts[context_type] = len(keys)
                    total_keys += len(keys)
                
                return {
                    "cache_type": "redis",
                    "total_keys": total_keys,
                    "key_counts_by_type": key_counts,
                    "redis_info": {
                        "used_memory": info.get("used_memory_human", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "uptime": info.get("uptime_in_seconds", 0)
                    }
                }
            else:
                # Memory cache stats
                key_counts = {
                    "learning_path": 0,
                    "module": 0,
                    "quiz": 0,
                    "progress": 0
                }
                
                for key in self._memory_cache.keys():
                    for context_type in key_counts.keys():
                        if context_type in key:
                            key_counts[context_type] += 1
                            break
                
                return {
                    "cache_type": "memory",
                    "total_keys": len(self._memory_cache),
                    "key_counts_by_type": key_counts,
                    "memory_cache_size": len(self._memory_cache)
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries (mainly for memory cache)"""
        try:
            if not self.redis_client:
                # Only needed for memory cache, Redis handles expiration automatically
                expired_keys = []
                now = datetime.now()
                
                for key, cache_entry in self._memory_cache.items():
                    if now >= cache_entry['expires']:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._memory_cache[key]
                
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                return len(expired_keys)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {str(e)}")
            return 0

    def clear_learning_path_context(self, user_id: str, team_id: Optional[str] = None) -> bool:
        """Clear cached learning path context (useful when data format changes)"""
        try:
            key = self._get_cache_key("learning_path", user_id, team_id)
            if self.redis_client:
                result = self.redis_client.delete(key)
                logger.debug(f"🗑️ Cleared learning path cache for user {user_id}, team {team_id}")
                return result > 0
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    logger.debug(f"🗑️ Cleared learning path cache for user {user_id}, team {team_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear learning path context: {str(e)}")
            return False

    def clear_all_user_context(self, user_id: str) -> bool:
        """Clear all cached context for a user"""
        try:
            if self.redis_client:
                # Find all keys for this user
                pattern = f"chat_context:*:{user_id}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    result = self.redis_client.delete(*keys)
                    logger.info(f"🗑️ Cleared {result} cache entries for user {user_id}")
                    return result > 0
            else:
                # Clear from memory cache
                keys_to_delete = [key for key in self._memory_cache.keys() if user_id in key]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                logger.info(f"🗑️ Cleared {len(keys_to_delete)} cache entries for user {user_id}")
                return len(keys_to_delete) > 0
            return False
        except Exception as e:
            logger.error(f"Failed to clear user context: {str(e)}")
            return False
