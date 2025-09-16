"""Pricing rule model for dynamic pricing."""

from sqlalchemy import Column, String, ForeignKey, DECIMAL, Time, Boolean, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import time, datetime
from typing import TYPE_CHECKING
from enum import Enum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.parking import ParkingLot


class PricingRuleType(str, Enum):
    """Types of pricing rules."""
    TIME_BASED = "time_based"
    DAY_BASED = "day_based"
    SEASONAL = "seasonal"
    DEMAND_BASED = "demand_based"


class DayOfWeek(str, Enum):
    """Days of the week."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class PricingRule(BaseModel):
    """Pricing rule model for dynamic pricing."""
    
    __tablename__ = "pricing_rules"
    
    lot_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("parking_lots.id", ondelete="CASCADE"), 
        nullable=False,
        doc="Reference to parking lot"
    )
    name = Column(
        String(255),
        nullable=False,
        doc="Name of the pricing rule"
    )
    vehicle_type = Column(
        String(20), 
        nullable=False,
        doc="Vehicle type this rule applies to"
    )
    rule_type = Column(
        String(20),
        nullable=False,
        default=PricingRuleType.TIME_BASED.value,
        doc="Type of pricing rule"
    )
    start_time = Column(
        Time, 
        nullable=True,
        doc="Start time for time-based rules"
    )
    end_time = Column(
        Time, 
        nullable=True,
        doc="End time for time-based rules"
    )
    days_of_week = Column(
        String(100),
        nullable=True,
        doc="Comma-separated days of week (monday,tuesday,etc.)"
    )
    price_per_hour = Column(
        DECIMAL(10, 2), 
        nullable=False,
        doc="Price per hour for this rule"
    )
    multiplier = Column(
        DECIMAL(5, 2),
        nullable=False,
        default=1.0,
        doc="Price multiplier (for surge pricing)"
    )
    min_charge = Column(
        DECIMAL(10, 2),
        nullable=True,
        doc="Minimum charge amount"
    )
    max_charge = Column(
        DECIMAL(10, 2),
        nullable=True,
        doc="Maximum charge amount"
    )
    is_active = Column(
        Boolean, 
        default=True,
        nullable=False,
        doc="Whether pricing rule is active"
    )
    priority = Column(
        String(10),
        nullable=False,
        default="normal",
        doc="Rule priority (high, normal, low)"
    )
    valid_from = Column(
        Time,
        nullable=True,
        doc="Rule valid from date"
    )
    valid_until = Column(
        Time,
        nullable=True,
        doc="Rule valid until date"
    )
    
    # Relationships
    lot: "ParkingLot" = relationship(
        "ParkingLot", 
        back_populates="pricing_rules"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"rule_type IN {tuple(e.value for e in PricingRuleType)}", 
            name="check_rule_type"
        ),
        CheckConstraint('price_per_hour > 0', name='check_price_positive'),
        CheckConstraint('multiplier > 0', name='check_multiplier_positive'),
        CheckConstraint('min_charge IS NULL OR min_charge >= 0', name='check_min_charge'),
        CheckConstraint('max_charge IS NULL OR max_charge >= 0', name='check_max_charge'),
        CheckConstraint(
            'min_charge IS NULL OR max_charge IS NULL OR min_charge <= max_charge', 
            name='check_min_max_charge'
        ),
        CheckConstraint(
            "priority IN ('high', 'normal', 'low')", 
            name="check_priority"
        ),
        UniqueConstraint(
            "lot_id", "vehicle_type", "start_time", "end_time", "rule_type", 
            name="unique_pricing_rule"
        ),
        Index('idx_pricing_lot_vehicle', 'lot_id', 'vehicle_type'),
        Index('idx_pricing_active', 'is_active'),
        Index('idx_pricing_time', 'start_time', 'end_time'),
        Index('idx_pricing_priority', 'priority'),
    )
    
    @property
    def effective_price(self) -> float:
        """Get effective price per hour with multiplier."""
        return float(self.price_per_hour * self.multiplier)
    
    @property
    def days_list(self) -> list[str]:
        """Get days of week as list."""
        if not self.days_of_week:
            return []
        return [day.strip() for day in self.days_of_week.split(',')]
    
    @days_list.setter
    def days_list(self, days: list[str]) -> None:
        """Set days of week from list."""
        self.days_of_week = ','.join(days) if days else None
    
    def applies_to_time(self, check_time: datetime) -> bool:
        """Check if rule applies to given time."""
        if not self.is_active:
            return False
        
        # Check date range
        if self.valid_from and check_time.date() < self.valid_from:
            return False
        if self.valid_until and check_time.date() > self.valid_until:
            return False
        
        # Check day of week
        if self.days_of_week:
            current_day = check_time.strftime('%A').lower()
            if current_day not in self.days_list:
                return False
        
        # Check time range
        if self.start_time and self.end_time:
            current_time = check_time.time()
            
            # Handle overnight rules (e.g., 22:00 to 06:00)
            if self.start_time > self.end_time:
                return current_time >= self.start_time or current_time <= self.end_time
            else:
                return self.start_time <= current_time <= self.end_time
        
        return True
    
    def calculate_charge(self, duration_hours: float) -> float:
        """Calculate charge for given duration."""
        base_charge = self.effective_price * duration_hours
        
        # Apply min/max constraints
        if self.min_charge:
            base_charge = max(base_charge, float(self.min_charge))
        if self.max_charge:
            base_charge = min(base_charge, float(self.max_charge))
        
        return round(base_charge, 2)
    
    @classmethod
    def create_peak_hour_rule(
        cls, 
        lot_id: UUID, 
        vehicle_type: str, 
        start_time: time, 
        end_time: time,
        peak_multiplier: float = 1.5
    ) -> "PricingRule":
        """Create a peak hour pricing rule."""
        return cls(
            lot_id=lot_id,
            name=f"Peak Hours {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}",
            vehicle_type=vehicle_type,
            rule_type=PricingRuleType.TIME_BASED.value,
            start_time=start_time,
            end_time=end_time,
            price_per_hour=5.0 if vehicle_type == "car" else 2.0,
            multiplier=peak_multiplier,
            priority="high"
        )
    
    @classmethod
    def create_weekend_rule(
        cls, 
        lot_id: UUID, 
        vehicle_type: str,
        weekend_multiplier: float = 1.2
    ) -> "PricingRule":
        """Create a weekend pricing rule."""
        return cls(
            lot_id=lot_id,
            name="Weekend Premium",
            vehicle_type=vehicle_type,
            rule_type=PricingRuleType.DAY_BASED.value,
            days_of_week="saturday,sunday",
            price_per_hour=5.0 if vehicle_type == "car" else 2.0,
            multiplier=weekend_multiplier,
            priority="normal"
        )
    
    def __str__(self) -> str:
        """String representation."""
        time_str = ""
        if self.start_time and self.end_time:
            time_str = f" {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        
        return f"{self.name} ({self.vehicle_type}){time_str} - ${self.effective_price:.2f}/hr"
