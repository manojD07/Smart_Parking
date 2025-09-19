"""Booking and slot allocation models."""

from sqlalchemy import Column, String, ForeignKey, DECIMAL, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional, List
from enum import Enum
import secrets
import string

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.parking import ParkingLot, ParkingSlot
    from app.models.slot_chunks import SlotTimeChunk


class BookingStatus(str, Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed" 
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NO_SHOW = "no_show"


class AllocationType(str, Enum):
    """Slot allocation type."""
    FULL = "full"  # Entire slot allocated (car or single bike)
    PARTIAL = "partial"  # Partial slot allocation (bike in car slot)


class Booking(BaseModel):
    """Booking model for parking reservations."""
    
    __tablename__ = "bookings"
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to user who made the booking"
    )
    lot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_lots.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to parking lot"
    )
    slot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_slots.id", ondelete="SET NULL"), 
        nullable=True,
        doc="Reference to allocated parking slot"
    )
    vehicle_type = Column(
        String(20), 
        nullable=False,
        doc="Type of vehicle"
    )
    vehicle_number = Column(
        String(20), 
        nullable=False,
        doc="Vehicle registration number"
    )
    start_time = Column(
        DateTime(timezone=True), 
        nullable=False,
        doc="Booking start time"
    )
    end_time = Column(
        DateTime(timezone=True), 
        nullable=False,
        doc="Booking end time"
    )
    total_amount = Column(
        DECIMAL(10, 2), 
        nullable=False,
        doc="Total amount for the booking"
    )
    status = Column(
        String(20), 
        nullable=False, 
        default=BookingStatus.CONFIRMED.value,
        doc="Current booking status"
    )
    booking_reference = Column(
        String(20), 
        unique=True, 
        nullable=False,
        doc="Unique booking reference code"
    )
    check_in_time = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Actual check-in time"
    )
    check_out_time = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Actual check-out time"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="bookings"
    )
    lot: Mapped["ParkingLot"] = relationship(
        "ParkingLot", 
        back_populates="bookings"
    )
    slot: Mapped[Optional["ParkingSlot"]] = relationship(
        "ParkingSlot", 
        back_populates="bookings"
    )
    slot_allocations: Mapped[List["SlotAllocation"]] = relationship(
        "SlotAllocation", 
        back_populates="booking",
        cascade="all, delete-orphan",
        lazy="select"
    )
    time_chunks: Mapped[List["SlotTimeChunk"]] = relationship(
        "SlotTimeChunk",
        back_populates="booking",
        lazy="select"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"status IN {tuple(e.value for e in BookingStatus)}", 
            name="check_booking_status"
        ),
        CheckConstraint('start_time < end_time', name='check_time_order'),
        CheckConstraint('total_amount >= 0', name='check_amount_positive'),
        Index('idx_booking_user_id', 'user_id'),
        Index('idx_booking_lot_id', 'lot_id'),
        Index('idx_booking_status', 'status'),
        Index('idx_booking_time_range', 'start_time', 'end_time'),
        Index('idx_booking_reference', 'booking_reference'),
        Index('idx_booking_vehicle', 'vehicle_number'),
    )
    
    @classmethod
    def generate_reference(cls) -> str:
        """Generate unique booking reference."""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))
    
    @property
    def duration_hours(self) -> float:
        """Get booking duration in hours."""
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    @property
    def is_active(self) -> bool:
        """Check if booking is currently active."""
        return self.status == BookingStatus.ACTIVE.value
    
    @property
    def is_expired(self) -> bool:
        """Check if booking has expired."""
        if self.status not in [BookingStatus.CONFIRMED.value, BookingStatus.ACTIVE.value]:
            return False
        return datetime.now(timezone.utc) > self.end_time
    
    @property
    def is_current(self) -> bool:
        """Check if booking is currently in progress."""
        now = datetime.now(timezone.utc)
        return (
            self.status in [BookingStatus.CONFIRMED.value, BookingStatus.ACTIVE.value] and
            self.start_time <= now <= self.end_time
        )
    
    @property
    def can_check_in(self) -> bool:
        """Check if user can check in."""
        now = datetime.now(timezone.utc)
        return (
            self.status == BookingStatus.CONFIRMED.value and
            self.check_in_time is None and
            self.start_time <= now
        )
    
    @property
    def can_check_out(self) -> bool:
        """Check if user can check out."""
        return (
            self.status == BookingStatus.ACTIVE.value and
            self.check_in_time is not None and
            self.check_out_time is None
        )
    
    @property
    def time_until_start(self) -> Optional[timedelta]:
        """Get time until booking starts."""
        if self.start_time > datetime.now(timezone.utc):
            return self.start_time - datetime.now(timezone.utc)
        return None
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get remaining time in booking."""
        if self.is_current:
            return self.end_time - datetime.now(timezone.utc)
        return None
    
    def can_cancel(self, min_notice_hours: int = 1) -> bool:
        """Check if booking can be cancelled."""
        if self.status not in [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value, BookingStatus.ACTIVE.value]:
            return False
        
        # Allow cancellation if start time is more than min_notice_hours away
        min_cancel_time = datetime.now(timezone.utc) + timedelta(hours=min_notice_hours)
        return self.start_time > min_cancel_time
    
    def cancel(self) -> None:
        """Cancel the booking."""
        if not self.can_cancel():
            raise ValueError("Booking cannot be cancelled")
        
        self.status = BookingStatus.CANCELLED.value
        if self.slot:
            self.slot.mark_available()
    
    def check_in(self) -> None:
        """Check in to the booking."""
        if not self.can_check_in:
            raise ValueError("Cannot check in at this time")
        
        self.check_in_time = datetime.now(timezone.utc)
        self.status = BookingStatus.ACTIVE.value
        if self.slot:
            self.slot.mark_occupied()
    
    def check_out(self) -> None:
        """Check out from the booking."""
        if not self.can_check_out:
            raise ValueError("Cannot check out at this time")
        
        self.check_out_time = datetime.now(timezone.utc)
        self.status = BookingStatus.COMPLETED.value
        if self.slot:
            self.slot.mark_available()
    
    def mark_expired(self) -> None:
        """Mark booking as expired."""
        self.status = BookingStatus.EXPIRED.value
        if self.slot:
            self.slot.mark_available()
    
    def mark_no_show(self) -> None:
        """Mark booking as no-show."""
        self.status = BookingStatus.NO_SHOW.value
        if self.slot:
            self.slot.mark_available()
    
    def __str__(self) -> str:
        """String representation."""
        return f"Booking {self.booking_reference} - {self.vehicle_type} ({self.status})"


class SlotAllocation(BaseModel):
    """Slot allocation model for tracking partial slot usage."""
    
    __tablename__ = "slot_allocations"
    
    booking_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("bookings.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to booking"
    )
    slot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_slots.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to parking slot"
    )
    allocation_type = Column(
        String(10), 
        nullable=False,
        doc="Type of allocation (full or partial)"
    )
    allocated_space = Column(
        String(50),
        nullable=True,
        doc="Description of allocated space (e.g., 'left_half', 'right_half')"
    )
    
    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking", 
        back_populates="slot_allocations"
    )
    slot: Mapped["ParkingSlot"] = relationship(
        "ParkingSlot", 
        back_populates="slot_allocations"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"allocation_type IN {tuple(e.value for e in AllocationType)}", 
            name="check_allocation_type"
        ),
        Index('idx_allocation_booking', 'booking_id'),
        Index('idx_allocation_slot', 'slot_id'),
        Index('idx_allocation_type', 'allocation_type'),
    )
    
    @property
    def is_full_allocation(self) -> bool:
        """Check if this is a full slot allocation."""
        return self.allocation_type == AllocationType.FULL.value
    
    @property
    def is_partial_allocation(self) -> bool:
        """Check if this is a partial slot allocation."""
        return self.allocation_type == AllocationType.PARTIAL.value
    
    @property
    def is_bike_in_car_slot(self) -> bool:
        """Check if this is a bike allocated to a car slot."""
        return (
            self.is_partial_allocation and
            self.booking and
            self.booking.vehicle_type == "bike" and
            self.slot and
            self.slot.slot_type == "car"
        )
    
    @property
    def space_designation_display(self) -> str:
        """Get human-readable space designation."""
        if not self.allocated_space:
            return "Full slot"
        
        space_map = {
            "left_half": "Left Half",
            "right_half": "Right Half",
            "front_half": "Front Half", 
            "back_half": "Back Half"
        }
        return space_map.get(self.allocated_space, self.allocated_space.replace("_", " ").title())
    
    def get_companion_space(self) -> Optional[str]:
        """Get the companion space designation for this allocation."""
        if not self.allocated_space:
            return None
        
        companion_map = {
            "left_half": "right_half",
            "right_half": "left_half",
            "front_half": "back_half",
            "back_half": "front_half"
        }
        return companion_map.get(self.allocated_space)
    
    def can_share_slot_with(self, other_vehicle_type: str) -> bool:
        """Check if this allocation can share slot with another vehicle."""
        if self.allocation_type == AllocationType.FULL.value:
            return False
        
        # Only bikes can share car slots
        return (
            self.booking and
            self.booking.vehicle_type == "bike" and
            other_vehicle_type == "bike" and
            self.slot and
            self.slot.slot_type == "car"
        )
    
    def __str__(self) -> str:
        """String representation."""
        space_info = f" ({self.space_designation_display})" if self.allocated_space else ""
        return f"Allocation {self.allocation_type}{space_info} for booking {self.booking.booking_reference if self.booking else 'Unknown'}"
