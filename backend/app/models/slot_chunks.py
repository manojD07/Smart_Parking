"""Smart slot time chunk models for flexible booking durations."""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index, Integer
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


class DemandLevel(str, Enum):
    """Demand level for dynamic chunk sizing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PEAK = "peak"


class GenerationStrategy(str, Enum):
    """Chunk generation strategy."""
    AUTO = "auto"
    MANUAL = "manual"
    DEMAND_BASED = "demand_based"


class SlotTimeChunk(BaseModel):
    """Smart time chunk model for flexible booking durations (1-240 minute chunks)."""
    
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
        doc="Chunk start time (1-minute precision)"
    )
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Chunk end time (1-minute precision)"
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
    
    # Smart chunk metadata
    chunk_size_minutes = Column(
        Integer,
        nullable=False,
        doc="Chunk duration in minutes (1, 5, 15, 30, 60, 120, 240)"
    )
    demand_level = Column(
        String(10),
        nullable=False,
        default=DemandLevel.MEDIUM.value,
        doc="Demand level when chunk was created"
    )
    generation_strategy = Column(
        String(20),
        nullable=False,
        default=GenerationStrategy.AUTO.value,
        doc="How this chunk was generated"
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
        # Flexible time constraints (1-minute precision)
        CheckConstraint(
            "EXTRACT(second FROM start_time) = 0 AND EXTRACT(microsecond FROM start_time) = 0",
            name="check_minute_precision"
        ),
        CheckConstraint(
            "EXTRACT(second FROM end_time) = 0 AND EXTRACT(microsecond FROM end_time) = 0",
            name="check_minute_precision_end"
        ),
        CheckConstraint(
            "end_time > start_time",
            name="check_chunk_time_order"
        ),
        CheckConstraint(
            "chunk_size_minutes IN (1, 5, 10, 15, 30, 60, 120, 240)",
            name="check_valid_chunk_sizes"
        ),
        CheckConstraint(
            "(end_time - start_time) = (chunk_size_minutes || ' minutes')::INTERVAL",
            name="check_chunk_duration_consistency"
        ),
        CheckConstraint(
            "chunk_size_minutes >= 1 AND chunk_size_minutes <= 240",
            name="check_chunk_size_range"
        ),
        CheckConstraint(
            f"status IN {tuple(e.value for e in ChunkStatus)}",
            name="check_chunk_status"
        ),
        CheckConstraint(
            f"demand_level IN {tuple(e.value for e in DemandLevel)}",
            name="check_demand_level"
        ),
        CheckConstraint(
            f"generation_strategy IN {tuple(e.value for e in GenerationStrategy)}",
            name="check_generation_strategy"
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
        Index("idx_slot_chunks_metadata", "chunk_size_minutes", "demand_level", "generation_strategy"),
        Index("idx_slot_chunks_time_range", "start_time", "end_time"),
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
        """Get chunk duration in minutes (flexible 1-240)."""
        return self.chunk_size_minutes
    
    @property
    def is_future(self) -> bool:
        """Check if chunk end time is in the future."""
        from datetime import datetime, timezone
        return self.end_time > datetime.now(timezone.utc)
    
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
        from datetime import datetime, timezone
        self.status = ChunkStatus.TEMP_RESERVED.value
        self.reserved_by = user_id
        self.reserved_at = datetime.now(timezone.utc)
        self.booking_id = None
    
    @property
    def is_high_demand(self) -> bool:
        """Check if chunk was created during high demand."""
        return self.demand_level in [DemandLevel.HIGH.value, DemandLevel.PEAK.value]
    
    @property 
    def is_micro_chunk(self) -> bool:
        """Check if this is a micro chunk (1-5 minutes)."""
        return self.chunk_size_minutes <= 5
    
    @property
    def is_standard_chunk(self) -> bool:
        """Check if this is a standard chunk (15-30 minutes)."""
        return 15 <= self.chunk_size_minutes <= 30
    
    @property
    def is_extended_chunk(self) -> bool:
        """Check if this is an extended chunk (60+ minutes)."""
        return self.chunk_size_minutes >= 60
    
    def get_tier_info(self) -> dict:
        """Get information about which duration tier this chunk belongs to."""
        if self.chunk_size_minutes <= 5:
            return {'tier': 'micro', 'description': 'High precision'}
        elif 5 < self.chunk_size_minutes <= 30:
            return {'tier': 'standard', 'description': 'Normal booking'}
        elif 30 < self.chunk_size_minutes <= 120:
            return {'tier': 'medium', 'description': 'Extended stay'}
        else:
            return {'tier': 'long', 'description': 'Long-term parking'}
    
    def can_accommodate_duration(self, desired_minutes: int) -> bool:
        """Check if this chunk can accommodate a desired duration."""
        return desired_minutes <= self.chunk_size_minutes
    
    def mark_booked_with_metadata(self, booking_id: UUID, demand_level: str = None) -> None:
        """Mark chunk as booked with optional demand level update."""
        self.mark_booked(booking_id)
        if demand_level:
            self.demand_level = demand_level
    
    def __repr__(self) -> str:
        return f"SlotTimeChunk({self.slot_id}, {self.start_time}-{self.end_time}, {self.status}, {self.chunk_size_minutes}min, {self.demand_level})"
