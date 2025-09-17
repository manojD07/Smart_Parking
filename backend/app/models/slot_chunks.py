"""Slot time chunk models for 30-minute booking slots."""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.parking import ParkingSlot
    from app.models.booking import Booking
    from app.models.user import User


class ChunkStatus(str, Enum):
    """Status of a time chunk."""
    AVAILABLE = "available"
    BOOKED = "booked"
    TEMP_RESERVED = "temp_reserved"
    MAINTENANCE = "maintenance"


class SlotTimeChunk(BaseModel):
    """Time chunk model for 30-minute parking slots."""
    
    __tablename__ = "slot_time_chunks"
    
    slot_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("parking_slots.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to parking slot"
    )
    start_time = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Chunk start time (must be :00 or :30)"
    )
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Chunk end time (must be :00 or :30)"
    )
    status = Column(
        String(20),
        nullable=False,
        default=ChunkStatus.AVAILABLE.value,
        doc="Current chunk status"
    )
    booking_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to booking if chunk is booked"
    )
    reserved_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who temporarily reserved this chunk"
    )
    reserved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the chunk was temporarily reserved"
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
        # 30-minute boundary constraints
        CheckConstraint(
            "EXTRACT(minute FROM start_time) IN (0, 30)",
            name="check_start_time_30_minute_boundary"
        ),
        CheckConstraint(
            "EXTRACT(minute FROM end_time) IN (0, 30)",
            name="check_end_time_30_minute_boundary"
        ),
        CheckConstraint(
            "end_time - start_time = INTERVAL '30 minutes'",
            name="check_30_minute_duration"
        ),
        CheckConstraint(
            "end_time > start_time",
            name="check_chunk_time_order"
        ),
        CheckConstraint(
            f"status IN {tuple(e.value for e in ChunkStatus)}",
            name="check_chunk_status"
        ),
        
        # Unique constraint for slot and time range
        UniqueConstraint("slot_id", "start_time", "end_time", name="unique_slot_time_chunk"),
        
        # Prevent overlapping reserved/booked chunks
        Index(
            "idx_no_overlapping_chunks",
            "slot_id", "start_time", "end_time",
            unique=True,
            postgresql_where="status IN ('booked', 'temp_reserved')"
        ),
        
        # Performance indexes
        Index("idx_slot_chunks_availability", "slot_id", "start_time", "end_time", "status"),
        Index("idx_slot_chunks_booking", "booking_id"),
        Index("idx_slot_chunks_reserved_by", "reserved_by", "reserved_at"),
    )
    
    @property
    def is_available(self) -> bool:
        """Check if chunk is available for booking."""
        return self.status == ChunkStatus.AVAILABLE.value
    
    @property
    def is_booked(self) -> bool:
        """Check if chunk is permanently booked."""
        return self.status == ChunkStatus.BOOKED.value
    
    @property
    def is_temp_reserved(self) -> bool:
        """Check if chunk is temporarily reserved."""
        return self.status == ChunkStatus.TEMP_RESERVED.value
    
    @property
    def duration_minutes(self) -> int:
        """Get chunk duration in minutes (always 30)."""
        return 30
    
    @property
    def is_future(self) -> bool:
        """Check if chunk end time is in the future."""
        from app.core.timezone import now as ist_now
        return self.end_time > ist_now()
    
    def mark_available(self) -> None:
        """Mark chunk as available."""
        self.status = ChunkStatus.AVAILABLE.value
        self.booking_id = None
        self.reserved_by = None
        self.reserved_at = None
    
    def mark_booked(self, booking_id: UUID) -> None:
        """Mark chunk as booked."""
        self.status = ChunkStatus.BOOKED.value
        self.booking_id = booking_id
        self.reserved_by = None
        self.reserved_at = None
    
    def mark_temp_reserved(self, user_id: UUID) -> None:
        """Mark chunk as temporarily reserved."""
        from app.core.timezone import now as ist_now
        self.status = ChunkStatus.TEMP_RESERVED.value
        self.reserved_by = user_id
        self.reserved_at = ist_now()
        self.booking_id = None
    
    def __repr__(self) -> str:
        return f"SlotTimeChunk({self.slot_id}, {self.start_time}-{self.end_time}, {self.status})"
