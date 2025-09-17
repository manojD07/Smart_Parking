"""Redis caching implementation for performance optimization."""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta, datetime
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class CacheService:
    """Redis-based caching service with fallback to in-memory cache."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.fallback_cache: Dict[str, Any] = {}
        self.default_ttl = 300  # 5 minutes
        self._setup_redis()
    
    def _setup_redis(self) -> None:
        """Setup Redis connection with error handling."""
        try:
            # Create connection pool for better performance
            pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            self.redis_client = redis.Redis(
                connection_pool=pool,
                decode_responses=False  # We'll handle encoding ourselves
            )
            
            logger.info("Redis cache service initialized")
            
        except Exception as e:
            logger.warning("Failed to initialize Redis, using fallback cache", error=str(e))
            self.redis_client = None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self.redis_client:
                value = await self.redis_client.get(self._make_key(key))
                if value is not None:
                    return self._deserialize(value)
            
            # Fallback to in-memory cache
            return self.fallback_cache.get(key, default)
            
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return self.fallback_cache.get(key, default)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            if ttl is None:
                ttl = self.default_ttl
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            if self.redis_client:
                serialized = self._serialize(value)
                success = await self.redis_client.setex(
                    self._make_key(key), 
                    ttl, 
                    serialized
                )
                if success:
                    return True
            
            # Fallback to in-memory cache (no TTL support)
            self.fallback_cache[key] = value
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            self.fallback_cache[key] = value
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            deleted = False
            
            if self.redis_client:
                result = await self.redis_client.delete(self._make_key(key))
                deleted = result > 0
            
            # Also remove from fallback cache
            if key in self.fallback_cache:
                del self.fallback_cache[key]
                deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            if key in self.fallback_cache:
                del self.fallback_cache[key]
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.redis_client:
                exists = await self.redis_client.exists(self._make_key(key))
                return exists > 0
            
            return key in self.fallback_cache
            
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return key in self.fallback_cache
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            if self.redis_client:
                redis_keys = [self._make_key(key) for key in keys]
                values = await self.redis_client.mget(redis_keys)
                
                result = {}
                for i, key in enumerate(keys):
                    if values[i] is not None:
                        result[key] = self._deserialize(values[i])
                
                return result
            
            # Fallback to in-memory cache
            return {key: self.fallback_cache.get(key) for key in keys if key in self.fallback_cache}
            
        except Exception as e:
            logger.error("Cache get_many error", keys=keys, error=str(e))
            return {key: self.fallback_cache.get(key) for key in keys if key in self.fallback_cache}
    
    async def set_many(
        self, 
        mapping: Dict[str, Any], 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set multiple values in cache."""
        try:
            if ttl is None:
                ttl = self.default_ttl
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            if self.redis_client:
                # Use pipeline for better performance
                pipe = self.redis_client.pipeline()
                
                for key, value in mapping.items():
                    serialized = self._serialize(value)
                    pipe.setex(self._make_key(key), ttl, serialized)
                
                await pipe.execute()
                return True
            
            # Fallback to in-memory cache
            self.fallback_cache.update(mapping)
            return True
            
        except Exception as e:
            logger.error("Cache set_many error", error=str(e))
            self.fallback_cache.update(mapping)
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(self._make_key(pattern))
                if keys:
                    return await self.redis_client.delete(*keys)
                return 0
            
            # Fallback - clear from in-memory cache
            deleted = 0
            keys_to_delete = [key for key in self.fallback_cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.fallback_cache[key]
                deleted += 1
            
            return deleted
            
        except Exception as e:
            logger.error("Cache clear_pattern error", pattern=pattern, error=str(e))
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        try:
            if self.redis_client:
                return await self.redis_client.incr(self._make_key(key), amount)
            
            # Fallback to in-memory cache
            current = self.fallback_cache.get(key, 0)
            new_value = current + amount
            self.fallback_cache[key] = new_value
            return new_value
            
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        try:
            if self.redis_client:
                return await self.redis_client.ttl(self._make_key(key))
            
            # Fallback cache doesn't support TTL
            return -1 if key in self.fallback_cache else -2
            
        except Exception as e:
            logger.error("Cache get_ttl error", key=key, error=str(e))
            return -2
    
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"smart_parking:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for simple types
            if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception:
            # Fallback to pickle
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to pickle
            return pickle.loads(value)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check cache service health."""
        health = {
            "redis_available": False,
            "fallback_cache_size": len(self.fallback_cache)
        }
        
        try:
            if self.redis_client:
                await self.redis_client.ping()
                health["redis_available"] = True
                
                info = await self.redis_client.info()
                health["redis_info"] = {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
        except Exception as e:
            health["redis_error"] = str(e)
        
        return health


# Global cache instance
cache = CacheService()


# High-level caching decorators and utilities

async def cached(
    key: str, 
    ttl: Optional[Union[int, timedelta]] = None,
    force_refresh: bool = False
):
    """Decorator for caching function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"func:{key}:{hash(str(args) + str(kwargs))}"
            
            if not force_refresh:
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


class ParkingCache:
    """Specialized cache for parking-related data."""
    
    @staticmethod
    async def get_lot_availability(lot_id: str) -> Optional[Dict[str, Any]]:
        """Get cached parking lot availability."""
        return await cache.get(f"lot_availability:{lot_id}")
    
    @staticmethod
    async def set_lot_availability(
        lot_id: str, 
        availability_data: Dict[str, Any], 
        ttl: int = 60
    ) -> bool:
        """Cache parking lot availability."""
        return await cache.set(f"lot_availability:{lot_id}", availability_data, ttl)
    
    @staticmethod
    async def invalidate_lot_availability(lot_id: str) -> bool:
        """Invalidate cached availability for a lot."""
        return await cache.delete(f"lot_availability:{lot_id}")
    
    @staticmethod
    async def get_pricing_rules(lot_id: str, vehicle_type: str) -> Optional[List[Dict]]:
        """Get cached pricing rules."""
        return await cache.get(f"pricing_rules:{lot_id}:{vehicle_type}")
    
    @staticmethod
    async def set_pricing_rules(
        lot_id: str, 
        vehicle_type: str, 
        rules: List[Dict], 
        ttl: int = 3600
    ) -> bool:
        """Cache pricing rules."""
        return await cache.set(f"pricing_rules:{lot_id}:{vehicle_type}", rules, ttl)
    
    @staticmethod
    async def invalidate_pricing_rules(lot_id: str) -> int:
        """Invalidate all cached pricing rules for a lot."""
        return await cache.clear_pattern(f"pricing_rules:{lot_id}:*")


class SessionCache:
    """Session-related caching utilities."""
    
    @staticmethod
    async def set_user_session(user_id: str, session_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """Cache user session data."""
        return await cache.set(f"session:{user_id}", session_data, ttl)
    
    @staticmethod
    async def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session data."""
        return await cache.get(f"session:{user_id}")
    
    @staticmethod
    async def invalidate_user_session(user_id: str) -> bool:
        """Invalidate user session."""
        return await cache.delete(f"session:{user_id}")


# Rate limiting cache utilities

class RateLimitCache:
    """Rate limiting using cache."""
    
    @staticmethod
    async def check_rate_limit(
        identifier: str, 
        limit: int, 
        window: int = 60
    ) -> Dict[str, Any]:
        """Check if identifier is within rate limit."""
        key = f"rate_limit:{identifier}"
        
        current_count = await cache.get(key, 0)
        
        if current_count >= limit:
            ttl = await cache.get_ttl(key)
            return {
                "allowed": False,
                "current": current_count,
                "limit": limit,
                "reset_in": ttl if ttl > 0 else window
            }
        
        # Increment counter
        new_count = await cache.increment(key)
        
        # Set TTL if this is the first request
        if new_count == 1:
            await cache.set(key, new_count, window)
        
        return {
            "allowed": True,
            "current": new_count,
            "limit": limit,
            "reset_in": await cache.get_ttl(key)
        }


# Chunk reservation cache utilities
class ChunkReservationCache:
    """Redis-based chunk reservation system with atomic locking."""
    
    @staticmethod
    async def reserve_chunks_atomic(
        chunk_ids: List[str],
        user_session_id: str,
        ttl_seconds: int = 600  # 10 minutes
    ) -> Dict[str, Any]:
        """Atomically reserve multiple chunks using Redis MULTI/EXEC."""
        try:
            if not cache.redis_client:
                raise Exception("Redis not available")
            
            # Phase 1: Check if any chunks are already reserved
            pipe = cache.redis_client.pipeline()
            for chunk_id in chunk_ids:
                key = f"chunk_lock:{chunk_id}"
                pipe.exists(key)
            
            existing_locks = await pipe.execute()
            
            if any(existing_locks):
                locked_chunks = [chunk_ids[i] for i, exists in enumerate(existing_locks) if exists]
                return {
                    "success": False,
                    "error": "Some chunks already reserved",
                    "locked_chunks": locked_chunks
                }
            
            # Phase 2: Atomic reservation using MULTI/EXEC
            pipe = cache.redis_client.pipeline()
            pipe.multi()
            
            for chunk_id in chunk_ids:
                key = f"chunk_lock:{chunk_id}"
                pipe.setex(key, ttl_seconds, user_session_id)
            
            # Also store the session info
            session_key = f"session:{user_session_id}"
            session_data = {
                "chunk_ids": chunk_ids,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            }
            pipe.setex(session_key, ttl_seconds, json.dumps(session_data))
            
            results = await pipe.execute()
            
            # Verify all operations succeeded
            if len(results) != len(chunk_ids) + 1:
                return {
                    "success": False,
                    "error": "Failed to acquire all locks"
                }
            
            logger.info(
                "Chunks reserved atomically",
                chunk_count=len(chunk_ids),
                session_id=user_session_id,
                ttl_seconds=ttl_seconds
            )
            
            return {
                "success": True,
                "session_id": user_session_id,
                "chunk_ids": chunk_ids,
                "expires_at": session_data["expires_at"],
                "ttl_seconds": ttl_seconds
            }
            
        except Exception as e:
            logger.error("Failed to reserve chunks atomically", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def release_chunks(
        chunk_ids: List[str],
        user_session_id: str
    ) -> bool:
        """Release reserved chunks."""
        try:
            if not cache.redis_client:
                return False
            
            pipe = cache.redis_client.pipeline()
            
            # Delete chunk locks
            for chunk_id in chunk_ids:
                key = f"chunk_lock:{chunk_id}"
                pipe.delete(key)
            
            # Delete session data
            session_key = f"session:{user_session_id}"
            pipe.delete(session_key)
            
            await pipe.execute()
            
            logger.info(
                "Chunks released",
                chunk_count=len(chunk_ids),
                session_id=user_session_id
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to release chunks", error=str(e))
            return False
    
    @staticmethod
    async def is_chunk_reserved(chunk_id: str) -> bool:
        """Check if a chunk is currently reserved in Redis."""
        try:
            if not cache.redis_client:
                return False
            
            key = f"chunk_lock:{chunk_id}"
            return bool(await cache.redis_client.exists(key))
            
        except Exception as e:
            logger.error("Failed to check chunk reservation", chunk_id=chunk_id, error=str(e))
            return False
    
    @staticmethod
    async def get_session_info(user_session_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation session information."""
        try:
            if not cache.redis_client:
                return None
            
            session_key = f"session:{user_session_id}"
            session_data = await cache.redis_client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get session info", session_id=user_session_id, error=str(e))
            return None
    
    @staticmethod
    async def extend_reservation(
        user_session_id: str,
        additional_seconds: int = 300  # 5 minutes
    ) -> bool:
        """Extend reservation TTL."""
        try:
            if not cache.redis_client:
                return False
            
            # Get current session data
            session_info = await ChunkReservationCache.get_session_info(user_session_id)
            if not session_info:
                return False
            
            chunk_ids = session_info["chunk_ids"]
            
            # Extend TTL for all related keys
            pipe = cache.redis_client.pipeline()
            
            for chunk_id in chunk_ids:
                key = f"chunk_lock:{chunk_id}"
                pipe.expire(key, additional_seconds)
            
            session_key = f"session:{user_session_id}"
            pipe.expire(session_key, additional_seconds)
            
            await pipe.execute()
            
            logger.info(
                "Reservation extended",
                session_id=user_session_id,
                additional_seconds=additional_seconds
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to extend reservation", error=str(e))
            return False
    
    @staticmethod
    async def cleanup_expired_reservations() -> int:
        """Manual cleanup of expired reservations (Redis TTL should handle this automatically)."""
        try:
            if not cache.redis_client:
                return 0
            
            # Get all chunk locks and session keys for monitoring
            chunk_keys = await cache.redis_client.keys("chunk_lock:*")
            session_keys = await cache.redis_client.keys("session:*")
            
            logger.info(
                "Redis reservation status",
                chunk_locks=len(chunk_keys),
                active_sessions=len(session_keys)
            )
            
            return len(session_keys)
            
        except Exception as e:
            logger.error("Failed to check reservation status", error=str(e))
            return 0
