"""Slot time chunk models for hourly booking system."""

from sqlalchemy import Column, String, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from enum import Enum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.parking import ParkingSlot
    from app.models.booking import Booking


class ChunkStatus(str, Enum):
    """Slot time chunk status enumeration."""
    AVAILABLE = "available"
    BOOKED = "booked"
    TEMP_RESERVED = "temp_reserved"


class SlotTimeChunk(BaseModel):
    """Time chunk model for hourly slot booking."""
    
    __tablename__ = "slot_time_chunks"
    
    slot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_slots.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to parking slot"
    )
    start_time = Column(
        DateTime(timezone=True), 
        nullable=False,
        doc="Chunk start time (hourly boundary)"
    )
    end_time = Column(
        DateTime(timezone=True), 
        nullable=False,
        doc="Chunk end time (hourly boundary)"
    )
    status = Column(
        String(20), 
        nullable=False, 
        default=ChunkStatus.AVAILABLE.value,
        doc="Chunk availability status"
    )
    booking_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("bookings.id", ondelete="SET NULL"), 
        nullable=True,
        doc="Reference to confirmed booking"
    )
    reserved_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        doc="User who temporarily reserved this chunk"
    )
    reserved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When chunk was temporarily reserved"
    )
    
    # Relationships
    slot: Mapped["ParkingSlot"] = relationship(
        "ParkingSlot", 
        back_populates="time_chunks"
    )
    booking: Mapped[Optional["Booking"]] = relationship(
        "Booking",
        back_populates="time_chunks"
    )
    reserved_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reserved_by]
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("status IN ('available', 'booked', 'temp_reserved')", name='check_chunk_status'),
        CheckConstraint('end_time > start_time', name='check_chunk_time_order'),
        Index('idx_slot_chunks_availability', 'slot_id', 'start_time', 'end_time', 'status'),
        Index('idx_slot_chunks_booking', 'booking_id'),
        Index('idx_slot_chunks_reserved_by', 'reserved_by', 'reserved_at'),
        Index(
            'idx_no_overlapping_chunks', 
            'slot_id', 'start_time', 'end_time',
            unique=True,
            postgresql_where=Column('status').in_(['booked', 'temp_reserved'])
        ),
    )
    
    @property
    def is_available(self) -> bool:
        """Check if chunk is available for booking."""
        return self.status == ChunkStatus.AVAILABLE.value
    
    @property
    def is_reserved(self) -> bool:
        """Check if chunk is temporarily reserved."""
        return self.status == ChunkStatus.TEMP_RESERVED.value
    
    @property
    def is_booked(self) -> bool:
        """Check if chunk is confirmed booked."""
        return self.status == ChunkStatus.BOOKED.value
    
    @property
    def duration_hours(self) -> float:
        """Get chunk duration in hours."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return 0.0
    
    def mark_available(self) -> None:
        """Mark chunk as available."""
        self.status = ChunkStatus.AVAILABLE.value
        self.booking_id = None
        self.reserved_by = None
        self.reserved_at = None
    
    def mark_temp_reserved(self, user_id: UUID) -> None:
        """Mark chunk as temporarily reserved."""
        self.status = ChunkStatus.TEMP_RESERVED.value
        self.reserved_by = user_id
        self.reserved_at = datetime.now()
    
    def mark_booked(self, booking_id: UUID) -> None:
        """Mark chunk as confirmed booked."""
        self.status = ChunkStatus.BOOKED.value
        self.booking_id = booking_id
        self.reserved_by = None
        self.reserved_at = None
    
    def __str__(self) -> str:
        """String representation."""
        return f"Chunk {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.status})"
