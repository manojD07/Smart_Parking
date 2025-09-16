"""Parking lot and slot models."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DECIMAL, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING, List, Optional
from enum import Enum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking, SlotAllocation
    from app.models.pricing import PricingRule


class VehicleType(str, Enum):
    """Supported vehicle types."""
    CAR = "car"
    BIKE = "bike"
    # Future extensions
    TRUCK = "truck"
    ELECTRIC_CAR = "electric_car"
    ELECTRIC_BIKE = "electric_bike"


class SlotStatus(str, Enum):
    """Parking slot status."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class ParkingLot(BaseModel):
    """Parking lot model."""
    
    __tablename__ = "parking_lots"
    
    name = Column(
        String(255), 
        nullable=False,
        doc="Parking lot name"
    )
    address = Column(
        String, 
        nullable=False,
        doc="Parking lot address"
    )
    latitude = Column(
        DECIMAL(10, 8), 
        nullable=False,
        doc="Latitude coordinate"
    )
    longitude = Column(
        DECIMAL(11, 8), 
        nullable=False,
        doc="Longitude coordinate"
    )
    total_car_slots = Column(
        Integer, 
        default=0,
        nullable=False,
        doc="Total number of car slots"
    )
    total_bike_slots = Column(
        Integer, 
        default=0,
        nullable=False,
        doc="Total number of bike slots"
    )
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        doc="Whether parking lot is active"
    )
    hourly_rate_car = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=5.00,
        doc="Base hourly rate for cars"
    )
    hourly_rate_bike = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=2.00,
        doc="Base hourly rate for bikes"
    )
    
    # Relationships
    slots: Mapped[List["ParkingSlot"]] = relationship(
        "ParkingSlot", 
        back_populates="lot",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    pricing_rules: Mapped[List["PricingRule"]] = relationship(
        "PricingRule", 
        back_populates="lot",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", 
        back_populates="lot",
        lazy="dynamic"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('total_car_slots >= 0', name='check_car_slots_positive'),
        CheckConstraint('total_bike_slots >= 0', name='check_bike_slots_positive'),
        CheckConstraint('hourly_rate_car > 0', name='check_car_rate_positive'),
        CheckConstraint('hourly_rate_bike > 0', name='check_bike_rate_positive'),
        Index('idx_parking_lot_location', 'latitude', 'longitude'),
        Index('idx_parking_lot_active', 'is_active'),
    )
    
    @property
    def total_slots(self) -> int:
        """Get total number of slots."""
        return self.total_car_slots + self.total_bike_slots
    
    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as tuple."""
        return (float(self.latitude), float(self.longitude))
    
    def get_available_slots_count(self, vehicle_type: VehicleType) -> int:
        """Get count of available slots for vehicle type."""
        return self.slots.filter(
            ParkingSlot.slot_type == vehicle_type.value,
            ParkingSlot.status == SlotStatus.AVAILABLE.value
        ).count()


class ParkingSlot(BaseModel):
    """Parking slot model."""
    
    __tablename__ = "parking_slots"
    
    lot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_lots.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to parking lot"
    )
    slot_number = Column(
        String(10), 
        nullable=False,
        doc="Slot number within the lot"
    )
    slot_type = Column(
        String(20), 
        nullable=False,
        doc="Type of vehicle this slot accommodates"
    )
    status = Column(
        String(20),
        nullable=False,
        default=SlotStatus.AVAILABLE.value,
        doc="Current status of the slot"
    )
    is_occupied = Column(
        Boolean, 
        default=False,
        nullable=False,
        doc="Whether slot is currently occupied"
    )
    is_reserved = Column(
        Boolean, 
        default=False,
        nullable=False,
        doc="Whether slot is reserved"
    )
    
    # Relationships
    lot: Mapped["ParkingLot"] = relationship(
        "ParkingLot", 
        back_populates="slots"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", 
        back_populates="slot",
        lazy="dynamic"
    )
    slot_allocations: Mapped[List["SlotAllocation"]] = relationship(
        "SlotAllocation", 
        back_populates="slot",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"slot_type IN {tuple(e.value for e in VehicleType)}", 
            name="check_slot_type"
        ),
        CheckConstraint(
            f"status IN {tuple(e.value for e in SlotStatus)}", 
            name="check_slot_status"
        ),
        UniqueConstraint("lot_id", "slot_number", name="unique_lot_slot"),
        Index('idx_slot_lot_type', 'lot_id', 'slot_type'),
        Index('idx_slot_status', 'status'),
        Index('idx_slot_availability', 'is_occupied', 'is_reserved', 'status'),
    )
    
    @property
    def is_available(self) -> bool:
        """Check if slot is available for booking."""
        return (
            self.status == SlotStatus.AVAILABLE.value and
            not self.is_occupied and
            not self.is_reserved
        )
    
    @property
    def vehicle_type_enum(self) -> VehicleType:
        """Get vehicle type as enum."""
        return VehicleType(self.slot_type)
    
    def can_accommodate_bikes(self) -> int:
        """Return how many bikes this slot can accommodate."""
        if self.slot_type == VehicleType.CAR.value and self.is_available:
            # Car slot can accommodate 2 bikes
            current_bikes = self.slot_allocations.filter(
                SlotAllocation.allocation_type == "partial"
            ).count()
            return max(0, 2 - current_bikes)
        elif self.slot_type == VehicleType.BIKE.value and self.is_available:
            return 1
        return 0
    
    def mark_occupied(self) -> None:
        """Mark slot as occupied."""
        self.is_occupied = True
        self.status = SlotStatus.OCCUPIED.value
    
    def mark_available(self) -> None:
        """Mark slot as available."""
        self.is_occupied = False
        self.is_reserved = False
        self.status = SlotStatus.AVAILABLE.value
    
    def mark_reserved(self) -> None:
        """Mark slot as reserved."""
        self.is_reserved = True
        self.status = SlotStatus.RESERVED.value
    
    def __str__(self) -> str:
        """String representation."""
        return f"Slot {self.slot_number} ({self.slot_type}) - {self.status}"
