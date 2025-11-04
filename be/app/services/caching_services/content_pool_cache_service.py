import redis
import json
import hashlib
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.core_schemas.preference_schema import PreferencesCreate

logger = get_logger(__name__)

class ContentPoolCacheService:
    """Service for caching content pools using Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        self.cache_ttl = 86400 * 7  # 7 days
        self.cache_prefix = "content_pool:"
        
    def _generate_cache_key(self, preferences: PreferencesCreate) -> str:
        """Generate a cache key based on preferences"""
        # Create a hash of the preferences to use as cache key
        cache_data = {
            "subject": preferences.subject,
            "experience": preferences.experience_level.value if hasattr(preferences.experience_level, 'value') else str(preferences.experience_level),
            "learning_style": preferences.learning_styles,
            "preferred_platforms": sorted(preferences.preferred_platforms),
            "desired_goals": preferences.goals
        }
        
        # Create hash from cache data
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"{self.cache_prefix}{cache_hash}"
    
    def cache_content_pool(self, preferences: PreferencesCreate, content_pool: List[Dict[str, Any]]) -> bool:
        """Cache content pool for given preferences"""
        try:
            cache_key = self._generate_cache_key(preferences)
            
            # Prepare cache data
            cache_data = {
                "preferences": {
                    "subject": preferences.subject,
                    "experience": preferences.experience_level.value if hasattr(preferences.experience_level, 'value') else str(preferences.experience_level),
                    "learning_style": preferences.learning_styles,
                    "preferred_platforms": preferences.preferred_platforms,
                    "desired_goals": preferences.goals
                },
                "content_pool": content_pool,
                "cached_at": json.dumps({"timestamp": "now"}),
                "pool_size": len(content_pool)
            }
            
            # Cache the data
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached content pool with {len(content_pool)} items for preferences hash: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching content pool: {str(e)}")
            return False
    
    def get_cached_content_pool(self, preferences: PreferencesCreate) -> Optional[List[Dict[str, Any]]]:
        """Get cached content pool for given preferences"""
        try:
            cache_key = self._generate_cache_key(preferences)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_dict = json.loads(cached_data)
                content_pool = cache_dict.get("content_pool", [])
                
                logger.info(f"Retrieved cached content pool with {len(content_pool)} items for preferences hash: {cache_key}")
                return content_pool
            else:
                logger.info(f"No cached content pool found for preferences hash: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving cached content pool: {str(e)}")
            return None
    
    def cache_learning_path_content_pool(self, learning_path_id: int, content_pool: List[Dict[str, Any]], used_content_ids: set) -> bool:
        """Cache content pool specifically for a learning path"""
        try:
            cache_key = f"{self.cache_prefix}lp_{learning_path_id}"
            
            cache_data = {
                "learning_path_id": learning_path_id,
                "content_pool": content_pool,
                "used_content_ids": list(used_content_ids),
                "available_content": [
                    content for content in content_pool 
                    if content.get("content_id") not in used_content_ids
                ],
                "cached_at": json.dumps({"timestamp": "now"}),
                "total_pool_size": len(content_pool),
                "available_pool_size": len(content_pool) - len(used_content_ids)
            }
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached learning path content pool for LP {learning_path_id}: {len(content_pool)} total, {len(used_content_ids)} used")
            return True
            
        except Exception as e:
            logger.error(f"Error caching learning path content pool: {str(e)}")
            return False
    
    def get_learning_path_content_pool(self, learning_path_id: int) -> Optional[Dict[str, Any]]:
        """Get cached content pool for a specific learning path"""
        try:
            cache_key = f"{self.cache_prefix}lp_{learning_path_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_dict = json.loads(cached_data)
                
                logger.info(f"Retrieved cached content pool for LP {learning_path_id}: {cache_dict['total_pool_size']} total, {cache_dict['available_pool_size']} available")
                return {
                    "content_pool": cache_dict["content_pool"],
                    "used_content_ids": set(cache_dict["used_content_ids"]),
                    "available_content": cache_dict["available_content"]
                }
            else:
                logger.info(f"No cached content pool found for LP {learning_path_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving learning path content pool: {str(e)}")
            return None
    
    def update_used_content_ids(self, learning_path_id: int, new_used_content_id: str) -> bool:
        """Update the used content IDs for a learning path"""
        try:
            cache_key = f"{self.cache_prefix}lp_{learning_path_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_dict = json.loads(cached_data)
                used_content_ids = set(cache_dict["used_content_ids"])
                used_content_ids.add(new_used_content_id)
                
                # Update available content
                content_pool = cache_dict["content_pool"]
                available_content = [
                    content for content in content_pool 
                    if content.get("content_id") not in used_content_ids
                ]
                
                cache_dict["used_content_ids"] = list(used_content_ids)
                cache_dict["available_content"] = available_content
                cache_dict["available_pool_size"] = len(available_content)
                
                # Update cache
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(cache_dict, default=str)
                )
                
                logger.info(f"Updated used content IDs for LP {learning_path_id}: {len(used_content_ids)} used, {len(available_content)} available")
                return True
            else:
                logger.warning(f"No cached content pool found for LP {learning_path_id} to update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating used content IDs: {str(e)}")
            return False
    
    def invalidate_cache(self, preferences: PreferencesCreate) -> bool:
        """Invalidate cached content pool for given preferences"""
        try:
            cache_key = self._generate_cache_key(preferences)
            result = self.redis_client.delete(cache_key)
            
            logger.info(f"Invalidated cache for preferences hash: {cache_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return False
    
    def invalidate_learning_path_cache(self, learning_path_id: int) -> bool:
        """Invalidate cached content pool for a learning path"""
        try:
            cache_key = f"{self.cache_prefix}lp_{learning_path_id}"
            result = self.redis_client.delete(cache_key)
            
            logger.info(f"Invalidated cache for LP {learning_path_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error invalidating learning path cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Get all cache keys
            cache_keys = self.redis_client.keys(f"{self.cache_prefix}*")
            
            general_caches = [key for key in cache_keys if not key.startswith(f"{self.cache_prefix}lp_")]
            learning_path_caches = [key for key in cache_keys if key.startswith(f"{self.cache_prefix}lp_")]
            
            return {
                "total_cached_pools": len(cache_keys),
                "general_preference_caches": len(general_caches),
                "learning_path_caches": len(learning_path_caches),
                "cache_ttl_seconds": self.cache_ttl,
                "cache_keys": cache_keys
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"error": str(e)}
