"""Redis-based distributed locking for atomic operations."""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Dict, Any
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class DistributedLock:
    """
    Redis-based distributed lock for preventing race conditions.
    
    Implements the Redlock algorithm for distributed locking with:
    - Automatic expiration to prevent deadlocks
    - Lock renewal for long-running operations
    - Retry logic with exponential backoff
    - Graceful fallback when Redis is unavailable
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        lock_key: str,
        timeout: float = 30.0,
        retry_delay: float = 0.1,
        max_retries: int = 10
    ):
        self.redis_client = redis_client
        self.lock_key = f"lock:{lock_key}"
        self.lock_value = str(uuid.uuid4())
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.acquired = False
        self.logger = logger.bind(lock_key=self.lock_key)
    
    async def acquire(self) -> bool:
        """
        Acquire the distributed lock.
        
        Returns:
            True if lock was acquired, False otherwise
        """
        try:
            for attempt in range(self.max_retries):
                # Try to acquire lock with SET NX EX (atomic operation)
                success = await self.redis_client.set(
                    self.lock_key,
                    self.lock_value,
                    nx=True,  # Only set if key doesn't exist
                    ex=int(self.timeout)  # Expire after timeout seconds
                )
                
                if success:
                    self.acquired = True
                    self.logger.info(
                        "Distributed lock acquired",
                        attempt=attempt + 1,
                        timeout=self.timeout
                    )
                    return True
                
                # Lock is held by someone else, wait and retry
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.debug(
                        "Lock acquisition failed, retrying",
                        attempt=attempt + 1,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
            
            self.logger.warning("Failed to acquire lock after all retries")
            return False
            
        except Exception as e:
            self.logger.error("Error acquiring lock", error=str(e))
            return False
    
    async def release(self) -> bool:
        """
        Release the distributed lock.
        
        Returns:
            True if lock was released successfully, False otherwise
        """
        if not self.acquired:
            return True
        
        try:
            # Use Lua script to ensure atomic check-and-delete
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            
            result = await self.redis_client.eval(
                lua_script,
                1,  # Number of keys
                self.lock_key,
                self.lock_value
            )
            
            success = bool(result)
            if success:
                self.acquired = False
                self.logger.info("Distributed lock released")
            else:
                self.logger.warning("Lock was not owned by this instance")
            
            return success
            
        except Exception as e:
            self.logger.error("Error releasing lock", error=str(e))
            return False
    
    async def extend(self, additional_time: float = 30.0) -> bool:
        """
        Extend the lock timeout.
        
        Args:
            additional_time: Additional seconds to extend the lock
            
        Returns:
            True if lock was extended successfully
        """
        if not self.acquired:
            return False
        
        try:
            # Use Lua script to extend lock only if we own it
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("EXPIRE", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            result = await self.redis_client.eval(
                lua_script,
                1,  # Number of keys
                self.lock_key,
                self.lock_value,
                int(additional_time)
            )
            
            success = bool(result)
            if success:
                self.logger.debug("Lock extended", additional_time=additional_time)
            
            return success
            
        except Exception as e:
            self.logger.error("Error extending lock", error=str(e))
            return False
    
    async def is_locked(self) -> bool:
        """Check if the lock is currently held (by anyone)."""
        try:
            exists = await self.redis_client.exists(self.lock_key)
            return bool(exists)
        except Exception as e:
            self.logger.error("Error checking lock status", error=str(e))
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        success = await self.acquire()
        if not success:
            raise LockAcquisitionError(f"Failed to acquire lock: {self.lock_key}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.release()


class LockManager:
    """
    Manager for creating and managing distributed locks.
    
    Provides high-level interface for common locking patterns.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.fallback_locks: Dict[str, asyncio.Lock] = {}
        self._setup_redis()
    
    def _setup_redis(self) -> None:
        """Setup Redis connection for locks."""
        try:
            pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=10,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            self.redis_client = redis.Redis(
                connection_pool=pool,
                decode_responses=True  # For lock values
            )
            
            logger.info("Redis lock manager initialized")
            
        except Exception as e:
            logger.warning("Failed to initialize Redis for locks, using local locks", error=str(e))
            self.redis_client = None
    
    @asynccontextmanager
    async def acquire_lock(
        self,
        lock_key: str,
        timeout: float = 30.0,
        retry_delay: float = 0.1,
        max_retries: int = 10
    ) -> AsyncGenerator[DistributedLock, None]:
        """
        Acquire a distributed lock using context manager.
        
        Args:
            lock_key: Unique identifier for the lock
            timeout: Lock timeout in seconds
            retry_delay: Initial retry delay in seconds
            max_retries: Maximum number of acquisition attempts
            
        Yields:
            DistributedLock instance
            
        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        if self.redis_client:
            # Use Redis distributed lock
            lock = DistributedLock(
                redis_client=self.redis_client,
                lock_key=lock_key,
                timeout=timeout,
                retry_delay=retry_delay,
                max_retries=max_retries
            )
            
            async with lock:
                yield lock
        else:
            # Fallback to local asyncio lock
            if lock_key not in self.fallback_locks:
                self.fallback_locks[lock_key] = asyncio.Lock()
            
            async with self.fallback_locks[lock_key]:
                # Create a mock lock object for compatibility
                mock_lock = MockDistributedLock(lock_key)
                yield mock_lock
    
    async def is_locked(self, lock_key: str) -> bool:
        """Check if a lock is currently held."""
        if self.redis_client:
            try:
                exists = await self.redis_client.exists(f"lock:{lock_key}")
                return bool(exists)
            except Exception:
                return False
        else:
            # Check local locks
            return lock_key in self.fallback_locks and self.fallback_locks[lock_key].locked()


class SlotLockManager:
    """
    Specialized lock manager for slot allocation operations.
    
    Provides semantic locking for parking slot operations.
    """
    
    def __init__(self, lock_manager: LockManager):
        self.lock_manager = lock_manager
        self.logger = logger.bind(manager="SlotLockManager")
    
    @asynccontextmanager
    async def lock_slot_allocation(
        self,
        slot_id: str,
        user_id: str,
        operation: str = "allocate"
    ) -> AsyncGenerator[DistributedLock, None]:
        """
        Lock a slot for allocation operations.
        
        Args:
            slot_id: Slot ID being allocated
            user_id: User ID performing the operation
            operation: Type of operation (allocate, release, etc.)
        """
        lock_key = f"slot_allocation:{slot_id}"
        
        self.logger.info(
            "Acquiring slot allocation lock",
            slot_id=slot_id,
            user_id=user_id,
            operation=operation
        )
        
        async with self.lock_manager.acquire_lock(
            lock_key=lock_key,
            timeout=30.0,  # 30 seconds for slot operations
            retry_delay=0.1,
            max_retries=20  # More retries for critical operations
        ) as lock:
            yield lock
    
    @asynccontextmanager
    async def lock_car_slot_for_bikes(
        self,
        slot_id: str,
        user_id: str
    ) -> AsyncGenerator[DistributedLock, None]:
        """
        Lock a car slot for bike allocation operations.
        
        Prevents race conditions when multiple bikes try to
        allocate to the same car slot simultaneously.
        """
        lock_key = f"car_slot_bikes:{slot_id}"
        
        self.logger.info(
            "Acquiring car slot bike allocation lock",
            slot_id=slot_id,
            user_id=user_id
        )
        
        async with self.lock_manager.acquire_lock(
            lock_key=lock_key,
            timeout=30.0,
            retry_delay=0.05,  # Faster retries for bike operations
            max_retries=30
        ) as lock:
            yield lock
    
    @asynccontextmanager
    async def lock_booking_creation(
        self,
        user_id: str,
        lot_id: str
    ) -> AsyncGenerator[DistributedLock, None]:
        """
        Lock booking creation for a user in a specific lot.
        
        Prevents duplicate bookings from the same user.
        """
        lock_key = f"booking_creation:{user_id}:{lot_id}"
        
        async with self.lock_manager.acquire_lock(
            lock_key=lock_key,
            timeout=60.0,  # Longer timeout for booking process
            retry_delay=0.2,
            max_retries=15
        ) as lock:
            yield lock


class MockDistributedLock:
    """Mock distributed lock for fallback scenarios."""
    
    def __init__(self, lock_key: str):
        self.lock_key = lock_key
        self.acquired = True  # Always acquired in fallback mode
    
    async def extend(self, additional_time: float = 30.0) -> bool:
        return True
    
    async def is_locked(self) -> bool:
        return True


class LockAcquisitionError(Exception):
    """Raised when a lock cannot be acquired."""
    pass


class LockTimeoutError(Exception):
    """Raised when a lock operation times out."""
    pass


# Global lock manager instance
lock_manager = LockManager()
slot_lock_manager = SlotLockManager(lock_manager)
