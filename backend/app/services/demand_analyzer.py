"""
Demand Analyzer Service for Smart Parking System

Calculates real-time demand levels based on:
- Booking frequency and patterns
- Availability scarcity
- Historical peak analysis
- User activity levels
- Revenue optimization factors
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, time
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, between
import asyncio

from app.models.slot_chunks import SlotTimeChunk, DemandLevel, ChunkStatus
from app.models.booking import Booking, BookingStatus
from app.models.parking import ParkingSlot, ParkingLot, VehicleType
from app.repositories.booking import BookingRepository
from app.repositories.parking import ParkingSlotRepository, ParkingLotRepository
from app.repositories.slot_chunks import SlotTimeChunkRepository
from app.core.config import get_settings
from app.core.cache import cache_manager

logger = structlog.get_logger(__name__)


class DemandMetric(str, Enum):
    """Types of demand metrics for analysis."""
    BOOKING_FREQUENCY = "booking_frequency"
    AVAILABILITY_SCARCITY = "availability_scarcity"
    HISTORICAL_PEAKS = "historical_peaks"
    USER_ACTIVITY = "user_activity"
    REVENUE_PRESSURE = "revenue_pressure"
    CONFLICT_RATE = "conflict_rate"


@dataclass
class DemandFactors:
    """Factors contributing to demand level calculation."""
    booking_frequency_score: float  # 0.0 - 1.0
    availability_scarcity_score: float  # 0.0 - 1.0
    historical_peak_score: float  # 0.0 - 1.0
    user_activity_score: float  # 0.0 - 1.0
    revenue_pressure_score: float  # 0.0 - 1.0
    conflict_rate_score: float  # 0.0 - 1.0
    time_of_day_multiplier: float  # 0.5 - 2.0
    day_of_week_multiplier: float  # 0.8 - 1.5
    
    @property
    def weighted_average(self) -> float:
        """Calculate weighted average demand score."""
        weights = {
            'booking_frequency': 0.25,
            'availability_scarcity': 0.20,
            'historical_peak': 0.15,
            'user_activity': 0.15,
            'revenue_pressure': 0.10,
            'conflict_rate': 0.15
        }
        
        raw_score = (
            self.booking_frequency_score * weights['booking_frequency'] +
            self.availability_scarcity_score * weights['availability_scarcity'] +
            self.historical_peak_score * weights['historical_peak'] +
            self.user_activity_score * weights['user_activity'] +
            self.revenue_pressure_score * weights['revenue_pressure'] +
            self.conflict_rate_score * weights['conflict_rate']
        )
        
        # Apply time-based multipliers
        adjusted_score = raw_score * self.time_of_day_multiplier * self.day_of_week_multiplier
        
        return min(max(adjusted_score, 0.0), 1.0)


@dataclass
class DemandAnalysisResult:
    """Result of demand analysis for a parking lot."""
    lot_id: UUID
    current_demand_level: DemandLevel
    demand_score: float  # 0.0 - 1.0
    demand_factors: DemandFactors
    trend_direction: str  # "increasing", "decreasing", "stable"
    peak_prediction: Optional[datetime]
    recommended_chunk_strategy: str
    confidence_level: float  # 0.0 - 1.0
    analysis_timestamp: datetime
    metadata: Dict
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DemandAnalyzer:
    """
    Service for analyzing parking demand in real-time.
    
    Calculates demand levels based on multiple factors and provides
    recommendations for chunk strategies and pricing optimization.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize demand analyzer."""
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.slot_repository = ParkingSlotRepository(session)
        self.lot_repository = ParkingLotRepository(session)
        self.chunk_repository = SlotTimeChunkRepository(session)
        from app.core.config import settings
        self.settings = settings
        self.logger = logger.bind(service="DemandAnalyzer")
        
        # Demand level thresholds
        self.demand_thresholds = {
            DemandLevel.LOW: (0.0, 0.25),
            DemandLevel.MEDIUM: (0.25, 0.65),
            DemandLevel.HIGH: (0.65, 0.85),
            DemandLevel.PEAK: (0.85, 1.0)
        }
        
        # Peak hour definitions
        self.peak_hours = {
            'morning': (7, 9),    # 7 AM - 9 AM
            'evening': (17, 19),  # 5 PM - 7 PM
            'weekend': (10, 16),  # 10 AM - 4 PM (weekends)
        }
        
        # Day of week multipliers
        self.day_multipliers = {
            0: 1.3,  # Monday
            1: 1.2,  # Tuesday
            2: 1.2,  # Wednesday
            3: 1.2,  # Thursday
            4: 1.4,  # Friday
            5: 0.9,  # Saturday
            6: 0.8   # Sunday
        }
    
    async def analyze_lot_demand(
        self, 
        lot_id: UUID,
        analysis_window_hours: int = 2,
        include_predictions: bool = True
    ) -> DemandAnalysisResult:
        """
        Perform comprehensive demand analysis for a parking lot.
        
        Args:
            lot_id: Parking lot to analyze
            analysis_window_hours: Hours of data to analyze
            include_predictions: Whether to include peak predictions
            
        Returns:
            DemandAnalysisResult with complete analysis
        """
        try:
            start_time = datetime.now(timezone.utc)
            self.logger.info(
                "Starting demand analysis",
                lot_id=lot_id,
                analysis_window_hours=analysis_window_hours
            )
            
            # Calculate individual demand factors
            demand_factors = await self._calculate_demand_factors(
                lot_id, analysis_window_hours
            )
            
            # Determine demand level and score
            demand_score = demand_factors.weighted_average
            current_demand_level = self._score_to_demand_level(demand_score)
            
            # Analyze demand trend
            trend_direction = await self._analyze_demand_trend(lot_id)
            
            # Predict next peak if requested
            peak_prediction = None
            if include_predictions:
                peak_prediction = await self._predict_next_peak(lot_id)
            
            # Generate recommendations
            recommended_strategy = self._recommend_chunk_strategy(
                current_demand_level, demand_factors
            )
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(demand_factors)
            
            # Generate metadata
            metadata = {
                "analysis_duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
                "data_points_analyzed": await self._count_data_points(lot_id, analysis_window_hours),
                "demand_breakdown": {
                    "booking_frequency": demand_factors.booking_frequency_score,
                    "availability_scarcity": demand_factors.availability_scarcity_score,
                    "historical_peak": demand_factors.historical_peak_score,
                    "user_activity": demand_factors.user_activity_score,
                    "revenue_pressure": demand_factors.revenue_pressure_score,
                    "conflict_rate": demand_factors.conflict_rate_score
                },
                "time_multipliers": {
                    "time_of_day": demand_factors.time_of_day_multiplier,
                    "day_of_week": demand_factors.day_of_week_multiplier
                }
            }
            
            result = DemandAnalysisResult(
                lot_id=lot_id,
                current_demand_level=current_demand_level,
                demand_score=demand_score,
                demand_factors=demand_factors,
                trend_direction=trend_direction,
                peak_prediction=peak_prediction,
                recommended_chunk_strategy=recommended_strategy,
                confidence_level=confidence_level,
                analysis_timestamp=datetime.now(timezone.utc),
                metadata=metadata
            )
            
            # Add warnings if needed
            if confidence_level < 0.6:
                result.warnings.append("Low confidence in demand analysis due to insufficient data")
            
            if demand_score > 0.9:
                result.warnings.append("Extremely high demand detected - consider emergency protocols")
            
            self.logger.info(
                "Demand analysis completed",
                lot_id=lot_id,
                demand_level=current_demand_level.value,
                demand_score=round(demand_score, 3),
                confidence=round(confidence_level, 3)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Error during demand analysis",
                lot_id=lot_id,
                error=str(e)
            )
            raise
    
    async def _calculate_demand_factors(
        self, 
        lot_id: UUID, 
        window_hours: int
    ) -> DemandFactors:
        """Calculate all demand factors for the analysis."""
        
        # Define time windows
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=window_hours)
        
        # Calculate each factor in parallel for performance
        tasks = [
            self._calculate_booking_frequency_score(lot_id, window_start, now),
            self._calculate_availability_scarcity_score(lot_id),
            self._calculate_historical_peak_score(lot_id, now),
            self._calculate_user_activity_score(lot_id, window_start, now),
            self._calculate_revenue_pressure_score(lot_id, window_start, now),
            self._calculate_conflict_rate_score(lot_id, window_start, now)
        ]
        
        scores = await asyncio.gather(*tasks)
        
        # Calculate time-based multipliers
        time_multiplier = self._calculate_time_of_day_multiplier(now)
        day_multiplier = self._calculate_day_of_week_multiplier(now)
        
        return DemandFactors(
            booking_frequency_score=scores[0],
            availability_scarcity_score=scores[1],
            historical_peak_score=scores[2],
            user_activity_score=scores[3],
            revenue_pressure_score=scores[4],
            conflict_rate_score=scores[5],
            time_of_day_multiplier=time_multiplier,
            day_of_week_multiplier=day_multiplier
        )
    
    async def _calculate_booking_frequency_score(
        self, 
        lot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> float:
        """Calculate booking frequency score (0.0 - 1.0)."""
        try:
            # Count bookings in the time window
            query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            )
            
            result = await self.session.execute(query)
            booking_count = result.scalar() or 0
            
            # Get total slots for normalization
            total_slots = await self._get_total_slots(lot_id)
            if total_slots == 0:
                return 0.0
            
            # Calculate frequency score (bookings per slot per hour)
            window_hours = (end_time - start_time).total_seconds() / 3600
            frequency = booking_count / (total_slots * window_hours) if window_hours > 0 else 0
            
            # Normalize to 0-1 scale (assume 1.0 booking/slot/hour is maximum)
            return min(frequency, 1.0)
            
        except Exception as e:
            self.logger.error("Error calculating booking frequency score", error=str(e))
            return 0.5  # Default fallback
    
    async def _calculate_availability_scarcity_score(self, lot_id: UUID) -> float:
        """Calculate availability scarcity score (0.0 - 1.0)."""
        try:
            # Get current slot availability
            total_slots = await self._get_total_slots(lot_id)
            available_slots = await self._get_available_slots(lot_id)
            
            if total_slots == 0:
                return 0.0
            
            availability_ratio = available_slots / total_slots
            scarcity_score = 1.0 - availability_ratio  # Invert: low availability = high scarcity
            
            return scarcity_score
            
        except Exception as e:
            self.logger.error("Error calculating availability scarcity score", error=str(e))
            return 0.5
    
    async def _calculate_historical_peak_score(self, lot_id: UUID, current_time: datetime) -> float:
        """Calculate historical peak score based on time patterns."""
        try:
            current_hour = current_time.hour
            current_weekday = current_time.weekday()
            
            # Check if current time matches known peak hours
            peak_score = 0.0
            
            # Morning peak
            if self.peak_hours['morning'][0] <= current_hour <= self.peak_hours['morning'][1]:
                peak_score = max(peak_score, 0.8)
            
            # Evening peak
            if self.peak_hours['evening'][0] <= current_hour <= self.peak_hours['evening'][1]:
                peak_score = max(peak_score, 0.9)
            
            # Weekend peak (Saturday/Sunday)
            if current_weekday >= 5 and self.peak_hours['weekend'][0] <= current_hour <= self.peak_hours['weekend'][1]:
                peak_score = max(peak_score, 0.7)
            
            # Friday evening boost
            if current_weekday == 4 and current_hour >= 16:  # Friday after 4 PM
                peak_score = max(peak_score, 0.85)
            
            return peak_score
            
        except Exception as e:
            self.logger.error("Error calculating historical peak score", error=str(e))
            return 0.3
    
    async def _calculate_user_activity_score(
        self, 
        lot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> float:
        """Calculate user activity score based on recent user interactions."""
        try:
            # Count unique users with bookings in the window
            query = select(func.count(func.distinct(Booking.user_id))).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time
                )
            )
            
            result = await self.session.execute(query)
            active_users = result.scalar() or 0
            
            # Normalize based on typical user activity (assume 50 active users is high)
            activity_score = min(active_users / 50.0, 1.0)
            
            return activity_score
            
        except Exception as e:
            self.logger.error("Error calculating user activity score", error=str(e))
            return 0.4
    
    async def _calculate_revenue_pressure_score(
        self, 
        lot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> float:
        """Calculate revenue pressure score based on pricing and occupancy."""
        try:
            # This would integrate with pricing service
            # For now, return a moderate score based on time patterns
            current_hour = datetime.now(timezone.utc).hour
            
            # Higher revenue pressure during business hours
            if 9 <= current_hour <= 17:  # Business hours
                return 0.7
            elif 17 <= current_hour <= 20:  # Evening rush
                return 0.8
            elif 20 <= current_hour <= 23:  # Night activities
                return 0.6
            else:  # Late night/early morning
                return 0.3
            
        except Exception as e:
            self.logger.error("Error calculating revenue pressure score", error=str(e))
            return 0.5
    
    async def _calculate_conflict_rate_score(
        self, 
        lot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> float:
        """Calculate conflict rate score based on booking conflicts."""
        try:
            # Count failed bookings (proxy for conflicts)
            failed_query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time,
                    Booking.status == BookingStatus.FAILED.value
                )
            )
            
            successful_query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            )
            
            failed_result = await self.session.execute(failed_query)
            successful_result = await self.session.execute(successful_query)
            
            failed_count = failed_result.scalar() or 0
            successful_count = successful_result.scalar() or 0
            total_attempts = failed_count + successful_count
            
            if total_attempts == 0:
                return 0.0
            
            conflict_rate = failed_count / total_attempts
            return min(conflict_rate * 2, 1.0)  # Amplify conflicts for demand indication
            
        except Exception as e:
            self.logger.error("Error calculating conflict rate score", error=str(e))
            return 0.2
    
    def _calculate_time_of_day_multiplier(self, current_time: datetime) -> float:
        """Calculate time of day multiplier (0.5 - 2.0)."""
        hour = current_time.hour
        
        if 7 <= hour <= 9:  # Morning rush
            return 1.8
        elif 12 <= hour <= 14:  # Lunch time
            return 1.4
        elif 17 <= hour <= 19:  # Evening rush
            return 2.0
        elif 20 <= hour <= 22:  # Evening activities
            return 1.3
        elif 0 <= hour <= 6:  # Late night
            return 0.5
        else:  # Regular hours
            return 1.0
    
    def _calculate_day_of_week_multiplier(self, current_time: datetime) -> float:
        """Calculate day of week multiplier (0.8 - 1.5)."""
        weekday = current_time.weekday()
        return self.day_multipliers.get(weekday, 1.0)
    
    def _score_to_demand_level(self, score: float) -> DemandLevel:
        """Convert demand score to demand level."""
        for level, (min_score, max_score) in self.demand_thresholds.items():
            if min_score <= score < max_score:
                return level
        return DemandLevel.PEAK  # Fallback for scores >= 0.85
    
    async def _analyze_demand_trend(self, lot_id: UUID) -> str:
        """Analyze demand trend direction."""
        try:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            two_hours_ago = now - timedelta(hours=2)
            
            # Count bookings in recent hours
            recent_bookings = await self._count_bookings_in_period(lot_id, hour_ago, now)
            earlier_bookings = await self._count_bookings_in_period(lot_id, two_hours_ago, hour_ago)
            
            if recent_bookings > earlier_bookings * 1.2:
                return "increasing"
            elif recent_bookings < earlier_bookings * 0.8:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error("Error analyzing demand trend", error=str(e))
            return "stable"
    
    async def _predict_next_peak(self, lot_id: UUID) -> Optional[datetime]:
        """Predict next peak time based on historical patterns."""
        try:
            now = datetime.now(timezone.utc)
            current_hour = now.hour
            
            # Simple prediction based on known peak hours
            next_peaks = []
            
            # Check for next morning peak (if not already past)
            if current_hour < self.peak_hours['morning'][0]:
                next_morning = now.replace(hour=self.peak_hours['morning'][0], minute=0, second=0, microsecond=0)
                next_peaks.append(next_morning)
            
            # Check for next evening peak (if not already past)
            if current_hour < self.peak_hours['evening'][0]:
                next_evening = now.replace(hour=self.peak_hours['evening'][0], minute=0, second=0, microsecond=0)
                next_peaks.append(next_evening)
            
            # Next day morning peak
            tomorrow_morning = (now + timedelta(days=1)).replace(
                hour=self.peak_hours['morning'][0], minute=0, second=0, microsecond=0
            )
            next_peaks.append(tomorrow_morning)
            
            # Return the next upcoming peak
            return min(next_peaks) if next_peaks else None
            
        except Exception as e:
            self.logger.error("Error predicting next peak", error=str(e))
            return None
    
    def _recommend_chunk_strategy(self, demand_level: DemandLevel, factors: DemandFactors) -> str:
        """Recommend chunk generation strategy based on demand analysis."""
        if demand_level == DemandLevel.PEAK:
            return "conflict_minimized"  # 1-minute precision for maximum flexibility
        elif demand_level == DemandLevel.HIGH:
            if factors.conflict_rate_score > 0.6:
                return "conflict_minimized"
            else:
                return "demand_optimized"
        elif demand_level == DemandLevel.MEDIUM:
            if factors.revenue_pressure_score > 0.7:
                return "revenue_optimized"
            else:
                return "hybrid"
        else:  # LOW demand
            return "space_optimized"  # Uniform chunks for predictable management
    
    def _calculate_confidence_level(self, factors: DemandFactors) -> float:
        """Calculate confidence level in the demand analysis."""
        # Base confidence on data quality and consistency
        base_confidence = 0.7
        
        # Reduce confidence if factors are contradictory
        factor_values = [
            factors.booking_frequency_score,
            factors.availability_scarcity_score,
            factors.user_activity_score,
            factors.conflict_rate_score
        ]
        
        # Calculate variance in factors
        mean_factor = sum(factor_values) / len(factor_values)
        variance = sum((x - mean_factor) ** 2 for x in factor_values) / len(factor_values)
        
        # High variance reduces confidence
        variance_penalty = min(variance * 0.5, 0.3)
        
        confidence = base_confidence - variance_penalty
        return min(max(confidence, 0.1), 1.0)
    
    async def _get_total_slots(self, lot_id: UUID) -> int:
        """Get total number of slots in a parking lot."""
        query = select(func.count(ParkingSlot.id)).where(ParkingSlot.lot_id == lot_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def _get_available_slots(self, lot_id: UUID) -> int:
        """Get number of currently available slots."""
        # This would need to check current bookings and slot status
        # Simplified for now
        total_slots = await self._get_total_slots(lot_id)
        
        # Count currently occupied slots (bookings in progress)
        now = datetime.now(timezone.utc)
        occupied_query = select(func.count(func.distinct(Booking.slot_id))).where(
            and_(
                Booking.lot_id == lot_id,
                Booking.start_time <= now,
                Booking.end_time > now,
                Booking.status.in_([
                    BookingStatus.CHECKED_IN.value,
                    BookingStatus.CONFIRMED.value
                ])
            )
        )
        
        result = await self.session.execute(occupied_query)
        occupied_slots = result.scalar() or 0
        
        return max(total_slots - occupied_slots, 0)
    
    async def _count_bookings_in_period(
        self, 
        lot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> int:
        """Count bookings in a specific time period."""
        query = select(func.count(Booking.id)).where(
            and_(
                Booking.lot_id == lot_id,
                Booking.created_at >= start_time,
                Booking.created_at <= end_time
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def _count_data_points(self, lot_id: UUID, window_hours: int) -> int:
        """Count total data points analyzed for metadata."""
        window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        
        # Count bookings + chunks + slots
        booking_count = await self._count_bookings_in_period(lot_id, window_start, datetime.now(timezone.utc))
        slot_count = await self._get_total_slots(lot_id)
        
        return booking_count + slot_count
    
    async def analyze_multiple_lots(
        self, 
        lot_ids: List[UUID],
        analysis_window_hours: int = 2
    ) -> List[DemandAnalysisResult]:
        """Analyze demand for multiple parking lots in parallel."""
        tasks = [
            self.analyze_lot_demand(lot_id, analysis_window_hours, include_predictions=False)
            for lot_id in lot_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "Failed to analyze lot demand",
                    lot_id=lot_ids[i],
                    error=str(result)
                )
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def get_system_wide_demand_summary(self) -> Dict:
        """Get system-wide demand summary across all lots."""
        try:
            # Get all active lots
            query = select(ParkingLot.id).where(ParkingLot.is_active == True)
            result = await self.session.execute(query)
            lot_ids = [row.id for row in result.scalars().all()]
            
            if not lot_ids:
                return {
                    "total_lots": 0,
                    "demand_distribution": {},
                    "average_demand_score": 0.0,
                    "system_status": "no_data"
                }
            
            # Analyze all lots
            analyses = await self.analyze_multiple_lots(lot_ids, analysis_window_hours=1)
            
            if not analyses:
                return {
                    "total_lots": len(lot_ids),
                    "demand_distribution": {},
                    "average_demand_score": 0.0,
                    "system_status": "analysis_failed"
                }
            
            # Calculate system-wide metrics
            demand_counts = {}
            total_score = 0.0
            
            for analysis in analyses:
                level = analysis.current_demand_level.value
                demand_counts[level] = demand_counts.get(level, 0) + 1
                total_score += analysis.demand_score
            
            avg_score = total_score / len(analyses)
            
            # Determine system status
            peak_lots = demand_counts.get(DemandLevel.PEAK.value, 0)
            high_lots = demand_counts.get(DemandLevel.HIGH.value, 0)
            
            if peak_lots > len(analyses) * 0.5:
                system_status = "high_demand_alert"
            elif (peak_lots + high_lots) > len(analyses) * 0.3:
                system_status = "elevated_demand"
            else:
                system_status = "normal_operations"
            
            return {
                "total_lots": len(lot_ids),
                "analyzed_lots": len(analyses),
                "demand_distribution": demand_counts,
                "average_demand_score": round(avg_score, 3),
                "system_status": system_status,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "peak_prediction": "system_wide_analysis_not_implemented"  # Future enhancement
            }
            
        except Exception as e:
            self.logger.error("Error getting system-wide demand summary", error=str(e))
            raise


# Factory function for dependency injection
def create_demand_analyzer(session: AsyncSession) -> DemandAnalyzer:
    """Factory function to create DemandAnalyzer instance."""
    return DemandAnalyzer(session)
