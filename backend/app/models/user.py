"""User model for authentication and user management."""

from sqlalchemy import Column, String, Boolean, Index, DECIMAL
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING, List

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking


class User(BaseModel):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    email = Column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True,
        doc="User email address (unique)"
    )
    password_hash = Column(
        String(255), 
        nullable=False,
        doc="Hashed password"
    )
    first_name = Column(
        String(100), 
        nullable=False,
        doc="User first name"
    )
    last_name = Column(
        String(100), 
        nullable=False,
        doc="User last name"
    )
    phone = Column(
        String(20),
        nullable=True,
        doc="User phone number"
    )
    is_admin = Column(
        Boolean, 
        default=False,
        nullable=False,
        doc="Whether user has admin privileges"
    )
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        doc="Whether user account is active"
    )
    total_spent = Column(
        DECIMAL(10, 2),
        default=0.00,
        nullable=False,
        doc="Total amount spent by user"
    )
    
    # Relationships
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_phone', 'phone'),
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (active)."""
        return self.is_active
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.full_name} ({self.email})"
