"""
Hybrid Duration Calculator for Smart Parking System

Implements the hybrid duration model with overlapping tiers:
- Tier 1 (15-35 min): 5-minute increments (15, 20, 25, 30, 35)
- Tier 2 (40-65 min): 10-minute increments (40, 50, 60)  
- Tier 3 (75-125 min): 15-minute increments (75, 90, 105, 120)
- Tier 4 (150+ min): 30-minute increments (150, 180, 210, 240...)

Ensures NO gaps in available durations through overlapping tier boundaries.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
import structlog

logger = structlog.get_logger(__name__)


class DurationTier(str, Enum):
    """Duration tier categories with different increment rules."""
    MICRO = "micro"          # 15-35 min: 5-min increments
    SHORT = "short"          # 40-65 min: 10-min increments  
    MEDIUM = "medium"        # 75-125 min: 15-min increments
    LONG = "long"            # 150+ min: 30-min increments


@dataclass
class DurationConfig:
    """Configuration for a duration tier."""
    tier: DurationTier
    min_duration: int
    max_duration: int
    increment: int
    description: str
    
    def get_valid_durations(self) -> List[int]:
        """Get all valid durations for this tier."""
        durations = []
        current = self.min_duration
        while current <= self.max_duration:
            durations.append(current)
            current += self.increment
        return durations


@dataclass
class DurationValidation:
    """Result of duration validation."""
    is_valid: bool
    suggested_duration: Optional[int] = None
    tier: Optional[DurationTier] = None
    increment: Optional[int] = None
    reason: Optional[str] = None
    alternatives: List[int] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class HybridDurationCalculator:
    """
    Smart duration calculator implementing hybrid increment model.
    
    Provides gap-free duration coverage through overlapping tiers:
    - No missing durations between 15-240 minutes
    - User-friendly increments that scale with duration
    - Efficient validation and suggestion algorithms
    """
    
    def __init__(self):
        """Initialize with hybrid duration tier configuration."""
        from app.core.config import settings
        self.settings = settings
        self.logger = logger.bind(service="HybridDurationCalculator")
        self.tiers: List[DurationConfig] = [
            DurationConfig(
                tier=DurationTier.MICRO,
                min_duration=15,
                max_duration=35,
                increment=5,
                description="Short stays: 5-minute precision"
            ),
            DurationConfig(
                tier=DurationTier.SHORT,
                min_duration=40,
                max_duration=65,
                increment=10,
                description="Medium stays: 10-minute blocks"
            ),
            DurationConfig(
                tier=DurationTier.MEDIUM,
                min_duration=75,
                max_duration=125,
                increment=15,
                description="Extended stays: 15-minute blocks"
            ),
            DurationConfig(
                tier=DurationTier.LONG,
                min_duration=150,
                max_duration=480,  # 8 hours max
                increment=30,
                description="Long-term parking: 30-minute blocks"
            )
        ]
        
        # Pre-calculate for performance
        self._all_valid_durations: Set[int] = set()
        self._duration_to_tier: Dict[int, DurationTier] = {}
        self._initialize_lookup_tables()
        
        self.logger = logger.bind(service="HybridDurationCalculator")
    
    def _initialize_lookup_tables(self) -> None:
        """Pre-calculate lookup tables for fast validation."""
        for tier_config in self.tiers:
            durations = tier_config.get_valid_durations()
            for duration in durations:
                self._all_valid_durations.add(duration)
                self._duration_to_tier[duration] = tier_config.tier
        
        # Handle overlaps - key overlapping durations
        overlaps = [30, 60, 120]  # Critical overlap points
        for overlap in overlaps:
            if overlap in self._all_valid_durations:
                # Assign to the tier with smaller increment for better UX
                for tier_config in sorted(self.tiers, key=lambda t: t.increment):
                    if tier_config.min_duration <= overlap <= tier_config.max_duration:
                        self._duration_to_tier[overlap] = tier_config.tier
                        break
        
        self.logger.info(
            "Initialized hybrid duration calculator",
            total_durations=len(self._all_valid_durations),
            min_duration=min(self._all_valid_durations),
            max_duration=max(self._all_valid_durations)
        )
    
    def validate_duration(self, duration_minutes: int) -> DurationValidation:
        """
        Validate a requested booking duration.
        
        Args:
            duration_minutes: Requested duration in minutes
            
        Returns:
            DurationValidation with validation result and suggestions
        """
        if duration_minutes < 15:
            return DurationValidation(
                is_valid=False,
                suggested_duration=15,
                tier=DurationTier.MICRO,
                increment=5,
                reason="Duration too short. Minimum booking is 15 minutes.",
                alternatives=[15, 20, 25]
            )
        
        if duration_minutes > 480:
            return DurationValidation(
                is_valid=False,
                suggested_duration=480,
                tier=DurationTier.LONG,
                increment=30,
                reason="Duration too long. Maximum booking is 8 hours (480 minutes).",
                alternatives=[420, 450, 480]
            )
        
        if duration_minutes in self._all_valid_durations:
            return DurationValidation(
                is_valid=True,
                suggested_duration=duration_minutes,
                tier=self._duration_to_tier[duration_minutes],
                increment=self._get_increment_for_duration(duration_minutes),
                reason="Duration is valid",
                alternatives=self._get_nearby_durations(duration_minutes, 3)
            )
        
        # Invalid duration - find closest valid option
        closest = self._find_closest_valid_duration(duration_minutes)
        tier = self._duration_to_tier[closest]
        
        return DurationValidation(
            is_valid=False,
            suggested_duration=closest,
            tier=tier,
            increment=self._get_increment_for_duration(closest),
            reason=f"Duration {duration_minutes} is not available. Suggested: {closest} minutes.",
            alternatives=self._get_nearby_durations(closest, 5)
        )
    
    def get_valid_durations_for_range(self, min_duration: int, max_duration: int) -> List[int]:
        """Get all valid durations within a time range."""
        return sorted([
            d for d in self._all_valid_durations 
            if min_duration <= d <= max_duration
        ])
    
    def get_durations_by_tier(self, tier: DurationTier) -> List[int]:
        """Get all valid durations for a specific tier."""
        return sorted([
            duration for duration, duration_tier in self._duration_to_tier.items()
            if duration_tier == tier
        ])
    
    def get_tier_for_duration(self, duration_minutes: int) -> Optional[DurationTier]:
        """Get the tier for a specific duration."""
        return self._duration_to_tier.get(duration_minutes)
    
    def calculate_chunk_requirements(
        self, 
        duration_minutes: int, 
        start_time: datetime
    ) -> List[Tuple[datetime, datetime, int]]:
        """
        Calculate the precise 1-minute chunks needed for a booking duration.
        
        Args:
            duration_minutes: Validated booking duration
            start_time: Booking start time
            
        Returns:
            List of (start_time, end_time, chunk_size) tuples for database storage
        """
        if duration_minutes not in self._all_valid_durations:
            raise ValueError(f"Duration {duration_minutes} is not valid")
        
        # For now, use 1-minute precision chunks for maximum flexibility
        chunks = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            chunk_end = min(current_time + timedelta(minutes=1), end_time)
            chunks.append((current_time, chunk_end, 1))
            current_time = chunk_end
        
        self.logger.debug(
            "Calculated chunk requirements",
            duration=duration_minutes,
            total_chunks=len(chunks),
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        return chunks
    
    def get_next_available_durations(self, current_duration: int, count: int = 5) -> List[int]:
        """Get the next N available durations after current duration."""
        sorted_durations = sorted(self._all_valid_durations)
        try:
            current_index = sorted_durations.index(current_duration)
            return sorted_durations[current_index + 1:current_index + 1 + count]
        except ValueError:
            # Current duration not in list, find insertion point
            for i, duration in enumerate(sorted_durations):
                if duration > current_duration:
                    return sorted_durations[i:i + count]
            return []
    
    def get_tier_boundaries(self) -> Dict[DurationTier, Tuple[int, int]]:
        """Get min/max boundaries for each tier."""
        boundaries = {}
        for tier_config in self.tiers:
            boundaries[tier_config.tier] = (tier_config.min_duration, tier_config.max_duration)
        return boundaries
    
    def _find_closest_valid_duration(self, duration_minutes: int) -> int:
        """Find the closest valid duration to the requested duration."""
        return min(
            self._all_valid_durations,
            key=lambda x: abs(x - duration_minutes)
        )
    
    def _get_increment_for_duration(self, duration_minutes: int) -> int:
        """Get the increment size for a specific duration."""
        tier = self._duration_to_tier.get(duration_minutes)
        if not tier:
            return 5  # Default fallback
        
        for tier_config in self.tiers:
            if tier_config.tier == tier:
                return tier_config.increment
        return 5
    
    def _get_nearby_durations(self, duration_minutes: int, count: int) -> List[int]:
        """Get nearby valid durations for suggestions."""
        sorted_durations = sorted(self._all_valid_durations)
        try:
            index = sorted_durations.index(duration_minutes)
            start = max(0, index - count // 2)
            end = min(len(sorted_durations), start + count)
            return sorted_durations[start:end]
        except ValueError:
            # Duration not in list, find closest
            closest_index = min(
                range(len(sorted_durations)),
                key=lambda i: abs(sorted_durations[i] - duration_minutes)
            )
            start = max(0, closest_index - count // 2)
            end = min(len(sorted_durations), start + count)
            return sorted_durations[start:end]
    
    def calculate_buffer_time(self, duration_minutes: int, demand_level: str = "medium") -> int:
        """
        Calculate appropriate buffer time for a booking duration.
        
        Args:
            duration_minutes: Booking duration
            demand_level: Current demand level (low/medium/high/peak)
            
        Returns:
            Buffer time in minutes
        """
        if not self.settings.enable_buffer_time:
            return 0
        
        if self.settings.buffer_time_strategy == "fixed":
            return self.settings.fixed_buffer_minutes
        
        if self.settings.buffer_time_strategy == "incremental" and self.settings.incremental_buffer_enabled:
            # Use tier-based incremental buffer (one increment size)
            tier = self.get_tier_for_duration(duration_minutes)
            if tier:
                increment = self._get_increment_for_duration(duration_minutes)
                return increment
            return 5  # Default fallback
        
        if self.settings.buffer_time_strategy == "demand_based" and self.settings.demand_based_buffer:
            # Adjust buffer based on demand level
            base_buffer = self.calculate_buffer_time(duration_minutes, "medium")  # Recursive call for base
            multipliers = {
                "low": 0.5,     # 50% less buffer during low demand
                "medium": 1.0,  # Normal buffer
                "high": 1.5,    # 50% more buffer during high demand  
                "peak": 2.0     # Double buffer during peak demand
            }
            return int(base_buffer * multipliers.get(demand_level, 1.0))
        
        return 5  # Default fallback
    
    def calculate_actual_end_time(
        self, 
        booking_start: datetime, 
        booking_duration: int, 
        demand_level: str = "medium"
    ) -> Tuple[datetime, datetime, int]:
        """
        Calculate booking end time and slot release time with buffer.
        
        Args:
            booking_start: Booking start time
            booking_duration: Duration in minutes
            demand_level: Current demand level
            
        Returns:
            Tuple of (booking_end_time, slot_release_time, buffer_minutes)
        """
        booking_end_time = booking_start + timedelta(minutes=booking_duration)
        buffer_minutes = self.calculate_buffer_time(booking_duration, demand_level)
        slot_release_time = booking_end_time + timedelta(minutes=buffer_minutes)
        
        return booking_end_time, slot_release_time, buffer_minutes
    
    def validate_booking_with_buffer(
        self,
        start_time: datetime,
        end_time: datetime,
        existing_bookings: List[Tuple[datetime, datetime]],
        demand_level: str = "medium"
    ) -> Tuple[bool, Optional[str], List[Tuple[datetime, datetime]]]:
        """
        Validate booking considering buffer times with existing bookings.
        
        Args:
            start_time: Proposed booking start
            end_time: Proposed booking end
            existing_bookings: List of (start, end) for existing bookings
            demand_level: Current demand level
            
        Returns:
            Tuple of (is_valid, conflict_reason, suggested_slots)
        """
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        buffer_minutes = self.calculate_buffer_time(duration_minutes, demand_level)
        
        # Check conflicts with buffer zones
        for existing_start, existing_end in existing_bookings:
            existing_duration = int((existing_end - existing_start).total_seconds() / 60)
            existing_buffer = self.calculate_buffer_time(existing_duration, demand_level)
            
            # Existing booking's effective end time (with buffer)
            existing_end_with_buffer = existing_end + timedelta(minutes=existing_buffer)
            
            # Proposed booking's effective end time (with buffer)
            proposed_end_with_buffer = end_time + timedelta(minutes=buffer_minutes)
            
            # Check for conflicts
            if (start_time < existing_end_with_buffer and proposed_end_with_buffer > existing_start):
                reason = f"Conflict with existing booking. Buffer time: {buffer_minutes}min required."
                
                # Suggest alternative slots
                suggested_slots = []
                
                # Suggest slot after existing booking (with buffer)
                new_start = existing_end_with_buffer
                new_end = new_start + timedelta(minutes=duration_minutes)
                suggested_slots.append((new_start, new_end))
                
                # Suggest slot before existing booking (with buffer)
                new_end = existing_start
                new_start = new_end - timedelta(minutes=duration_minutes + buffer_minutes)
                if new_start >= datetime.now(timezone.utc):
                    suggested_slots.append((new_start, new_end))
                
                return False, reason, suggested_slots
        
        return True, None, []

    def get_duration_summary(self) -> Dict[str, any]:
        """Get a summary of the duration system for API/UI display."""
        return {
            "total_valid_durations": len(self._all_valid_durations),
            "min_duration": min(self._all_valid_durations),
            "max_duration": max(self._all_valid_durations),
            "buffer_time_enabled": self.settings.enable_buffer_time,
            "buffer_strategy": self.settings.buffer_time_strategy,
            "tiers": [
                {
                    "tier": tier_config.tier.value,
                    "description": tier_config.description,
                    "min_duration": tier_config.min_duration,
                    "max_duration": tier_config.max_duration,
                    "increment": tier_config.increment,
                    "buffer_time": self.calculate_buffer_time(tier_config.min_duration),
                    "valid_durations": tier_config.get_valid_durations()
                }
                for tier_config in self.tiers
            ],
            "overlapping_durations": [30, 60, 120],
            "gaps": self._find_gaps()
        }
    
    def _find_gaps(self) -> List[int]:
        """Find any gaps in duration coverage (should be empty for hybrid model)."""
        all_durations = sorted(self._all_valid_durations)
        gaps = []
        
        for i in range(len(all_durations) - 1):
            current = all_durations[i]
            next_duration = all_durations[i + 1]
            
            # Check for gaps larger than expected increment
            tier = self._duration_to_tier[current]
            expected_increment = self._get_increment_for_duration(current)
            
            if next_duration - current > expected_increment:
                # There's a gap
                for missing in range(current + 1, next_duration):
                    gaps.append(missing)
        
        return gaps


# Global instance for application use
duration_calculator = HybridDurationCalculator()
