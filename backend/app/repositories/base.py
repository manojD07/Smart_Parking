"""Base repository with common CRUD operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Sequence
from uuid import UUID
import structlog

from app.models.base import BaseModel

logger = structlog.get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """Initialize repository with session and model."""
        self.session = session
        self.model = model
        self.logger = logger.bind(repository=self.__class__.__name__)
    
    async def create(self, **kwargs) -> T:
        """Create a new record."""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            
            self.logger.info("Created record", model=self.model.__name__, id=instance.id)
            return instance
            
        except Exception as e:
            self.logger.error("Failed to create record", error=str(e))
            raise
    
    async def get_by_id(self, id: UUID, load_relationships: bool = False) -> Optional[T]:
        """Get record by ID."""
        try:
            query = select(self.model).where(self.model.id == id)
            
            # Load relationships if requested
            if load_relationships:
                query = self._add_relationship_loading(query)
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get record by ID", id=id, error=str(e))
            raise
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        load_relationships: bool = False,
        **filters
    ) -> List[T]:
        """Get multiple records with pagination and filters."""
        try:
            query = select(self.model)
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, **filters)
            
            # Load relationships if requested
            if load_relationships:
                query = self._add_relationship_loading(query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get multiple records", error=str(e))
            raise
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update record by ID."""
        try:
            # Remove None values and id from kwargs
            update_data = {k: v for k, v in kwargs.items() if v is not None and k != 'id'}
            
            if not update_data:
                return await self.get_by_id(id)
            
            query = (
                update(self.model)
                .where(self.model.id == id)
                .values(**update_data)
                .returning(self.model)
            )
            
            result = await self.session.execute(query)
            updated_record = result.scalar_one_or_none()
            
            if updated_record:
                await self.session.flush()
                await self.session.refresh(updated_record)
                self.logger.info("Updated record", id=id, fields=list(update_data.keys()))
            
            return updated_record
            
        except Exception as e:
            self.logger.error("Failed to update record", id=id, error=str(e))
            raise
    
    async def delete(self, id: UUID) -> bool:
        """Delete record by ID."""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            
            deleted = result.rowcount > 0
            if deleted:
                self.logger.info("Deleted record", id=id)
            
            return deleted
            
        except Exception as e:
            self.logger.error("Failed to delete record", id=id, error=str(e))
            raise
    
    async def exists(self, **filters) -> bool:
        """Check if record exists with given filters."""
        try:
            query = select(func.count(self.model.id))
            
            if filters:
                query = self._apply_filters(query, **filters)
            
            result = await self.session.execute(query)
            count = result.scalar()
            
            return count > 0
            
        except Exception as e:
            self.logger.error("Failed to check existence", error=str(e))
            raise
    
    async def count(self, **filters) -> int:
        """Count records with given filters."""
        try:
            query = select(func.count(self.model.id))
            
            if filters:
                query = self._apply_filters(query, **filters)
            
            result = await self.session.execute(query)
            return result.scalar()
            
        except Exception as e:
            self.logger.error("Failed to count records", error=str(e))
            raise
    
    async def get_or_create(self, defaults: Optional[Dict] = None, **kwargs) -> tuple[T, bool]:
        """Get existing record or create new one."""
        try:
            # Try to get existing record
            query = select(self.model)
            query = self._apply_filters(query, **kwargs)
            
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
            
            if instance:
                return instance, False
            
            # Create new record
            create_data = {**kwargs}
            if defaults:
                create_data.update(defaults)
            
            instance = await self.create(**create_data)
            return instance, True
            
        except Exception as e:
            self.logger.error("Failed to get or create record", error=str(e))
            raise
    
    async def bulk_create(self, objects: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records in bulk."""
        try:
            instances = [self.model(**obj) for obj in objects]
            self.session.add_all(instances)
            await self.session.flush()
            
            self.logger.info("Bulk created records", count=len(instances))
            return instances
            
        except Exception as e:
            self.logger.error("Failed to bulk create records", error=str(e))
            raise
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in bulk."""
        try:
            if not updates:
                return 0
            
            # Group updates by fields to update
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                record_id = update_data.pop('id')
                await self.update(record_id, **update_data)
            
            self.logger.info("Bulk updated records", count=len(updates))
            return len(updates)
            
        except Exception as e:
            self.logger.error("Failed to bulk update records", error=str(e))
            raise
    
    def _apply_filters(self, query, **filters):
        """Apply filters to query."""
        for field, value in filters.items():
            if hasattr(self.model, field):
                if isinstance(value, list):
                    query = query.where(getattr(self.model, field).in_(value))
                elif isinstance(value, dict):
                    # Handle complex filters like {'gt': 10}, {'like': '%test%'}
                    for op, val in value.items():
                        if op == 'gt':
                            query = query.where(getattr(self.model, field) > val)
                        elif op == 'gte':
                            query = query.where(getattr(self.model, field) >= val)
                        elif op == 'lt':
                            query = query.where(getattr(self.model, field) < val)
                        elif op == 'lte':
                            query = query.where(getattr(self.model, field) <= val)
                        elif op == 'like':
                            query = query.where(getattr(self.model, field).ilike(val))
                        elif op == 'in':
                            query = query.where(getattr(self.model, field).in_(val))
                        elif op == 'not_in':
                            query = query.where(~getattr(self.model, field).in_(val))
                else:
                    query = query.where(getattr(self.model, field) == value)
        
        return query
    
    def _add_relationship_loading(self, query):
        """Add relationship loading to query. Override in subclasses."""
        return query
