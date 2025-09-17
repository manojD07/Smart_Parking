"""Base model with common fields and utilities."""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timezone
from typing import Any
import uuid

from app.core.database import Base


class TimestampMixin:
    """Mixin for adding timestamp fields."""
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        doc="Unique identifier"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + 's'
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
