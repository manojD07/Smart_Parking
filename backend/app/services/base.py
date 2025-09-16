"""Base service class with common functionality."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.core.exceptions import ServiceError, NotFoundError, ValidationError

logger = structlog.get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R', bound=BaseRepository)


class BaseService(Generic[T, R], ABC):
    """Base service class providing common business logic patterns."""
    
    def __init__(self, repository: R):
        """Initialize service with repository."""
        self.repository = repository
        self.logger = logger.bind(service=self.__class__.__name__)
    
    async def get_by_id(self, id: UUID, load_relationships: bool = False) -> Optional[T]:
        """Get entity by ID."""
        try:
            entity = await self.repository.get_by_id(id, load_relationships)
            if not entity:
                raise NotFoundError(f"{self._get_entity_name()} not found with id: {id}")
            return entity
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error("Failed to get entity by ID", id=id, error=str(e))
            raise ServiceError(f"Failed to retrieve {self._get_entity_name()}")
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        load_relationships: bool = False,
        **filters
    ) -> List[T]:
        """Get multiple entities with pagination and filters."""
        try:
            # Validate pagination parameters
            if skip < 0:
                raise ValidationError("Skip parameter must be non-negative")
            if limit <= 0 or limit > 1000:
                raise ValidationError("Limit must be between 1 and 1000")
            
            return await self.repository.get_multi(
                skip=skip, 
                limit=limit, 
                load_relationships=load_relationships,
                **filters
            )
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error("Failed to get multiple entities", error=str(e))
            raise ServiceError(f"Failed to retrieve {self._get_entity_name()}s")
    
    async def create(self, **kwargs) -> T:
        """Create new entity."""
        try:
            # Validate creation data
            await self._validate_create_data(**kwargs)
            
            # Perform pre-creation logic
            await self._before_create(**kwargs)
            
            # Create entity
            entity = await self.repository.create(**kwargs)
            
            # Perform post-creation logic
            await self._after_create(entity)
            
            self.logger.info("Created entity", entity_id=entity.id)
            return entity
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error("Failed to create entity", error=str(e))
            raise ServiceError(f"Failed to create {self._get_entity_name()}")
    
    async def update(self, id: UUID, **kwargs) -> T:
        """Update entity by ID."""
        try:
            # Check if entity exists
            existing_entity = await self.repository.get_by_id(id)
            if not existing_entity:
                raise NotFoundError(f"{self._get_entity_name()} not found with id: {id}")
            
            # Validate update data
            await self._validate_update_data(existing_entity, **kwargs)
            
            # Perform pre-update logic
            await self._before_update(existing_entity, **kwargs)
            
            # Update entity
            updated_entity = await self.repository.update(id, **kwargs)
            
            # Perform post-update logic
            await self._after_update(updated_entity, existing_entity)
            
            self.logger.info("Updated entity", entity_id=id)
            return updated_entity
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Failed to update entity", id=id, error=str(e))
            raise ServiceError(f"Failed to update {self._get_entity_name()}")
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        try:
            # Check if entity exists
            existing_entity = await self.repository.get_by_id(id)
            if not existing_entity:
                raise NotFoundError(f"{self._get_entity_name()} not found with id: {id}")
            
            # Validate deletion
            await self._validate_delete(existing_entity)
            
            # Perform pre-deletion logic
            await self._before_delete(existing_entity)
            
            # Delete entity
            deleted = await self.repository.delete(id)
            
            if deleted:
                # Perform post-deletion logic
                await self._after_delete(existing_entity)
                self.logger.info("Deleted entity", entity_id=id)
            
            return deleted
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Failed to delete entity", id=id, error=str(e))
            raise ServiceError(f"Failed to delete {self._get_entity_name()}")
    
    async def exists(self, **filters) -> bool:
        """Check if entity exists with given filters."""
        try:
            return await self.repository.exists(**filters)
            
        except Exception as e:
            self.logger.error("Failed to check entity existence", error=str(e))
            raise ServiceError(f"Failed to check {self._get_entity_name()} existence")
    
    async def count(self, **filters) -> int:
        """Count entities with given filters."""
        try:
            return await self.repository.count(**filters)
            
        except Exception as e:
            self.logger.error("Failed to count entities", error=str(e))
            raise ServiceError(f"Failed to count {self._get_entity_name()}s")
    
    # Template methods for subclasses to override
    
    async def _validate_create_data(self, **kwargs) -> None:
        """Validate data before creating entity. Override in subclasses."""
        pass
    
    async def _validate_update_data(self, existing_entity: T, **kwargs) -> None:
        """Validate data before updating entity. Override in subclasses."""
        pass
    
    async def _validate_delete(self, entity: T) -> None:
        """Validate before deleting entity. Override in subclasses."""
        pass
    
    async def _before_create(self, **kwargs) -> None:
        """Execute logic before creating entity. Override in subclasses."""
        pass
    
    async def _after_create(self, entity: T) -> None:
        """Execute logic after creating entity. Override in subclasses."""
        pass
    
    async def _before_update(self, existing_entity: T, **kwargs) -> None:
        """Execute logic before updating entity. Override in subclasses."""
        pass
    
    async def _after_update(self, updated_entity: T, previous_entity: T) -> None:
        """Execute logic after updating entity. Override in subclasses."""
        pass
    
    async def _before_delete(self, entity: T) -> None:
        """Execute logic before deleting entity. Override in subclasses."""
        pass
    
    async def _after_delete(self, entity: T) -> None:
        """Execute logic after deleting entity. Override in subclasses."""
        pass
    
    def _get_entity_name(self) -> str:
        """Get human-readable entity name. Override in subclasses."""
        return "Entity"


class TransactionalService:
    """Mixin for services that need transaction management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_in_transaction(self, operation):
        """Execute operation within a transaction."""
        try:
            result = await operation()
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise
