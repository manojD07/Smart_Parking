"""
Utilization Analytics Service for Smart Parking System

Provides comprehensive analytics on:
- Space utilization efficiency
- Revenue optimization metrics
- User booking pattern analysis
- Conflict frequency tracking
- Performance benchmarking
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, time
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, between, case, text
from decimal import Decimal
import asyncio

from app.models.slot_chunks import SlotTimeChunk, DemandLevel, ChunkStatus
from app.models.booking import Booking, BookingStatus
from app.models.parking import ParkingSlot, ParkingLot, VehicleType
from app.models.payment import Payment, PaymentStatus
from app.repositories.booking import BookingRepository
from app.repositories.parking import ParkingSlotRepository
from app.repositories.slot_chunks import SlotTimeChunkRepository
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class AnalyticsPeriod(str, Enum):
    """Time periods for analytics analysis."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class UtilizationMetric(str, Enum):
    """Types of utilization metrics."""
    OCCUPANCY_RATE = "occupancy_rate"
    REVENUE_PER_HOUR = "revenue_per_hour"
    BOOKING_EFFICIENCY = "booking_efficiency"
    CONFLICT_RATE = "conflict_rate"
    SPACE_TURNOVER = "space_turnover"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class UtilizationMetrics:
    """Core utilization metrics for a time period."""
    occupancy_rate: float  # 0.0 - 1.0
    revenue_per_hour: Decimal
    booking_efficiency: float  # successful bookings / total attempts
    average_booking_duration: float  # minutes
    space_turnover_rate: float  # bookings per slot per day
    conflict_rate: float  # 0.0 - 1.0
    chunk_utilization_rate: float  # 0.0 - 1.0
    buffer_time_effectiveness: float  # 0.0 - 1.0


@dataclass
class PerformanceBenchmark:
    """Performance benchmarks for comparison."""
    metric_name: str
    current_value: float
    benchmark_value: float
    performance_ratio: float  # current / benchmark
    trend_direction: str  # "improving", "declining", "stable"
    recommendation: str


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    lot_id: UUID
    analysis_period: AnalyticsPeriod
    start_time: datetime
    end_time: datetime
    utilization_metrics: UtilizationMetrics
    performance_benchmarks: List[PerformanceBenchmark]
    peak_hours: List[Dict]
    booking_patterns: Dict
    revenue_analysis: Dict
    optimization_opportunities: List[Dict]
    confidence_level: float
    report_timestamp: datetime
    metadata: Dict


class UtilizationAnalytics:
    """
    Service for analyzing parking space utilization and performance.
    
    Provides detailed analytics on space usage, revenue optimization,
    and operational efficiency with benchmarking and recommendations.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize utilization analytics service."""
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.slot_repository = ParkingSlotRepository(session)
        self.chunk_repository = SlotTimeChunkRepository(session)
        from app.core.config import settings
        self.settings = settings
        self.logger = logger.bind(service="UtilizationAnalytics")
        
        # Performance benchmarks (industry standards)
        self.benchmarks = {
            "occupancy_rate": 0.75,      # 75% target occupancy
            "booking_efficiency": 0.90,  # 90% successful bookings
            "conflict_rate": 0.05,       # 5% max conflict rate
            "revenue_per_hour": Decimal("25.00"),  # Target revenue per hour
            "space_turnover": 3.0,       # 3 bookings per slot per day
            "chunk_utilization": 0.80    # 80% chunk utilization
        }
    
    async def generate_utilization_report(
        self,
        lot_id: UUID,
        period: AnalyticsPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> AnalyticsReport:
        """
        Generate comprehensive utilization analytics report.
        
        Args:
            lot_id: Parking lot to analyze
            period: Analysis period granularity
            start_time: Analysis start time (optional)
            end_time: Analysis end time (optional)
            
        Returns:
            AnalyticsReport with complete analysis
        """
        try:
            # Define analysis time window
            if not start_time or not end_time:
                start_time, end_time = self._get_default_time_window(period)
            
            self.logger.info(
                "Generating utilization report",
                lot_id=lot_id,
                period=period.value,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )
            
            # Calculate core metrics in parallel
            tasks = [
                self._calculate_utilization_metrics(lot_id, start_time, end_time),
                self._analyze_peak_hours(lot_id, start_time, end_time),
                self._analyze_booking_patterns(lot_id, start_time, end_time),
                self._analyze_revenue_performance(lot_id, start_time, end_time),
                self._identify_optimization_opportunities(lot_id, start_time, end_time)
            ]
            
            results = await asyncio.gather(*tasks)
            
            utilization_metrics = results[0]
            peak_hours = results[1]
            booking_patterns = results[2]
            revenue_analysis = results[3]
            optimization_opportunities = results[4]
            
            # Generate performance benchmarks
            performance_benchmarks = self._generate_performance_benchmarks(utilization_metrics)
            
            # Calculate confidence level
            confidence_level = self._calculate_report_confidence(
                lot_id, start_time, end_time, utilization_metrics
            )
            
            # Generate metadata
            metadata = {
                "data_points_analyzed": await self._count_data_points(lot_id, start_time, end_time),
                "analysis_duration_hours": (end_time - start_time).total_seconds() / 3600,
                "lot_total_slots": await self._get_total_slots(lot_id),
                "period_granularity": period.value,
                "report_generation_time": datetime.now(timezone.utc).isoformat()
            }
            
            report = AnalyticsReport(
                lot_id=lot_id,
                analysis_period=period,
                start_time=start_time,
                end_time=end_time,
                utilization_metrics=utilization_metrics,
                performance_benchmarks=performance_benchmarks,
                peak_hours=peak_hours,
                booking_patterns=booking_patterns,
                revenue_analysis=revenue_analysis,
                optimization_opportunities=optimization_opportunities,
                confidence_level=confidence_level,
                report_timestamp=datetime.now(timezone.utc),
                metadata=metadata
            )
            
            self.logger.info(
                "Utilization report generated successfully",
                lot_id=lot_id,
                occupancy_rate=round(utilization_metrics.occupancy_rate, 3),
                revenue_per_hour=float(utilization_metrics.revenue_per_hour),
                confidence_level=round(confidence_level, 3)
            )
            
            return report
            
        except Exception as e:
            self.logger.error(
                "Error generating utilization report",
                lot_id=lot_id,
                period=period.value,
                error=str(e)
            )
            raise
    
    async def _calculate_utilization_metrics(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> UtilizationMetrics:
        """Calculate core utilization metrics."""
        
        # Calculate metrics in parallel
        tasks = [
            self._calculate_occupancy_rate(lot_id, start_time, end_time),
            self._calculate_revenue_per_hour(lot_id, start_time, end_time),
            self._calculate_booking_efficiency(lot_id, start_time, end_time),
            self._calculate_average_booking_duration(lot_id, start_time, end_time),
            self._calculate_space_turnover_rate(lot_id, start_time, end_time),
            self._calculate_conflict_rate(lot_id, start_time, end_time),
            self._calculate_chunk_utilization_rate(lot_id, start_time, end_time),
            self._calculate_buffer_time_effectiveness(lot_id, start_time, end_time)
        ]
        
        metrics = await asyncio.gather(*tasks)
        
        return UtilizationMetrics(
            occupancy_rate=metrics[0],
            revenue_per_hour=metrics[1],
            booking_efficiency=metrics[2],
            average_booking_duration=metrics[3],
            space_turnover_rate=metrics[4],
            conflict_rate=metrics[5],
            chunk_utilization_rate=metrics[6],
            buffer_time_effectiveness=metrics[7]
        )
    
    async def _calculate_occupancy_rate(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate occupancy rate for the time period."""
        try:
            total_slots = await self._get_total_slots(lot_id)
            if total_slots == 0:
                return 0.0
            
            # Calculate total possible slot-hours
            period_hours = (end_time - start_time).total_seconds() / 3600
            total_slot_hours = total_slots * period_hours
            
            # Calculate occupied slot-hours
            query = select(
                func.sum(
                    func.extract('epoch', 
                        func.least(Booking.end_time, end_time) - 
                        func.greatest(Booking.start_time, start_time)
                    ) / 3600
                )
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.start_time < end_time,
                    Booking.end_time > start_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            )
            
            result = await self.session.execute(query)
            occupied_hours = result.scalar() or 0
            
            return min(occupied_hours / total_slot_hours, 1.0) if total_slot_hours > 0 else 0.0
            
        except Exception as e:
            self.logger.error("Error calculating occupancy rate", error=str(e))
            return 0.0
    
    async def _calculate_revenue_per_hour(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Decimal:
        """Calculate revenue per hour for the time period."""
        try:
            # Calculate total revenue from payments
            query = select(func.sum(Payment.amount)).join(
                Booking, Payment.booking_id == Booking.id
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Payment.created_at >= start_time,
                    Payment.created_at <= end_time,
                    Payment.status == PaymentStatus.COMPLETED.value
                )
            )
            
            result = await self.session.execute(query)
            total_revenue = result.scalar() or Decimal('0.00')
            
            # Calculate time period in hours
            period_hours = (end_time - start_time).total_seconds() / 3600
            
            return total_revenue / Decimal(str(period_hours)) if period_hours > 0 else Decimal('0.00')
            
        except Exception as e:
            self.logger.error("Error calculating revenue per hour", error=str(e))
            return Decimal('0.00')
    
    async def _calculate_booking_efficiency(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate booking success rate."""
        try:
            # Count successful bookings
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
            
            # Count total booking attempts
            total_query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time
                )
            )
            
            successful_result = await self.session.execute(successful_query)
            total_result = await self.session.execute(total_query)
            
            successful_count = successful_result.scalar() or 0
            total_count = total_result.scalar() or 0
            
            return successful_count / total_count if total_count > 0 else 0.0
            
        except Exception as e:
            self.logger.error("Error calculating booking efficiency", error=str(e))
            return 0.0
    
    async def _calculate_average_booking_duration(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate average booking duration in minutes."""
        try:
            query = select(
                func.avg(
                    func.extract('epoch', Booking.end_time - Booking.start_time) / 60
                )
            ).where(
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
            avg_duration = result.scalar() or 0.0
            
            return float(avg_duration)
            
        except Exception as e:
            self.logger.error("Error calculating average booking duration", error=str(e))
            return 0.0
    
    async def _calculate_space_turnover_rate(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate space turnover rate (bookings per slot per day)."""
        try:
            total_slots = await self._get_total_slots(lot_id)
            if total_slots == 0:
                return 0.0
            
            # Count total bookings
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
            total_bookings = result.scalar() or 0
            
            # Calculate period in days
            period_days = (end_time - start_time).total_seconds() / (24 * 3600)
            
            return total_bookings / (total_slots * period_days) if period_days > 0 else 0.0
            
        except Exception as e:
            self.logger.error("Error calculating space turnover rate", error=str(e))
            return 0.0
    
    async def _calculate_conflict_rate(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate booking conflict rate."""
        try:
            # Count failed bookings as proxy for conflicts
            failed_query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time,
                    Booking.status == BookingStatus.FAILED.value
                )
            )
            
            total_query = select(func.count(Booking.id)).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.created_at >= start_time,
                    Booking.created_at <= end_time
                )
            )
            
            failed_result = await self.session.execute(failed_query)
            total_result = await self.session.execute(total_query)
            
            failed_count = failed_result.scalar() or 0
            total_count = total_result.scalar() or 0
            
            return failed_count / total_count if total_count > 0 else 0.0
            
        except Exception as e:
            self.logger.error("Error calculating conflict rate", error=str(e))
            return 0.0
    
    async def _calculate_chunk_utilization_rate(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate chunk utilization rate."""
        try:
            # Count total chunks in period
            total_chunks_query = select(func.count(SlotTimeChunk.id)).join(
                ParkingSlot, SlotTimeChunk.slot_id == ParkingSlot.id
            ).where(
                and_(
                    ParkingSlot.lot_id == lot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time
                )
            )
            
            # Count utilized chunks
            utilized_chunks_query = select(func.count(SlotTimeChunk.id)).join(
                ParkingSlot, SlotTimeChunk.slot_id == ParkingSlot.id
            ).where(
                and_(
                    ParkingSlot.lot_id == lot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time,
                    SlotTimeChunk.status.in_([
                        ChunkStatus.BOOKED.value,
                        ChunkStatus.TEMP_RESERVED.value
                    ])
                )
            )
            
            total_result = await self.session.execute(total_chunks_query)
            utilized_result = await self.session.execute(utilized_chunks_query)
            
            total_chunks = total_result.scalar() or 0
            utilized_chunks = utilized_result.scalar() or 0
            
            return utilized_chunks / total_chunks if total_chunks > 0 else 0.0
            
        except Exception as e:
            self.logger.error("Error calculating chunk utilization rate", error=str(e))
            return 0.0
    
    async def _calculate_buffer_time_effectiveness(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate buffer time effectiveness (preventing conflicts)."""
        try:
            # This would analyze if buffer times prevented conflicts
            # For now, return a baseline based on conflict rate
            conflict_rate = await self._calculate_conflict_rate(lot_id, start_time, end_time)
            
            # Effectiveness = 1 - conflict_rate (inverse relationship)
            return max(1.0 - conflict_rate, 0.0)
            
        except Exception as e:
            self.logger.error("Error calculating buffer time effectiveness", error=str(e))
            return 0.5
    
    def _generate_performance_benchmarks(
        self,
        metrics: UtilizationMetrics
    ) -> List[PerformanceBenchmark]:
        """Generate performance benchmarks comparing current metrics to targets."""
        benchmarks = []
        
        # Occupancy rate benchmark
        occupancy_ratio = metrics.occupancy_rate / self.benchmarks["occupancy_rate"]
        benchmarks.append(PerformanceBenchmark(
            metric_name="Occupancy Rate",
            current_value=metrics.occupancy_rate,
            benchmark_value=self.benchmarks["occupancy_rate"],
            performance_ratio=occupancy_ratio,
            trend_direction=self._determine_trend("occupancy", occupancy_ratio),
            recommendation=self._get_occupancy_recommendation(occupancy_ratio)
        ))
        
        # Booking efficiency benchmark
        efficiency_ratio = metrics.booking_efficiency / self.benchmarks["booking_efficiency"]
        benchmarks.append(PerformanceBenchmark(
            metric_name="Booking Efficiency",
            current_value=metrics.booking_efficiency,
            benchmark_value=self.benchmarks["booking_efficiency"],
            performance_ratio=efficiency_ratio,
            trend_direction=self._determine_trend("efficiency", efficiency_ratio),
            recommendation=self._get_efficiency_recommendation(efficiency_ratio)
        ))
        
        # Conflict rate benchmark (lower is better)
        conflict_ratio = self.benchmarks["conflict_rate"] / max(metrics.conflict_rate, 0.001)
        benchmarks.append(PerformanceBenchmark(
            metric_name="Conflict Rate",
            current_value=metrics.conflict_rate,
            benchmark_value=self.benchmarks["conflict_rate"],
            performance_ratio=conflict_ratio,
            trend_direction=self._determine_trend("conflict", conflict_ratio),
            recommendation=self._get_conflict_recommendation(metrics.conflict_rate)
        ))
        
        # Revenue per hour benchmark
        revenue_ratio = float(metrics.revenue_per_hour) / float(self.benchmarks["revenue_per_hour"])
        benchmarks.append(PerformanceBenchmark(
            metric_name="Revenue per Hour",
            current_value=float(metrics.revenue_per_hour),
            benchmark_value=float(self.benchmarks["revenue_per_hour"]),
            performance_ratio=revenue_ratio,
            trend_direction=self._determine_trend("revenue", revenue_ratio),
            recommendation=self._get_revenue_recommendation(revenue_ratio)
        ))
        
        return benchmarks
    
    def _determine_trend(self, metric_type: str, ratio: float) -> str:
        """Determine trend direction based on performance ratio."""
        if ratio >= 1.1:
            return "improving"
        elif ratio <= 0.9:
            return "declining"
        else:
            return "stable"
    
    def _get_occupancy_recommendation(self, ratio: float) -> str:
        """Get recommendation for occupancy performance."""
        if ratio < 0.7:
            return "Increase marketing efforts and consider dynamic pricing to boost occupancy"
        elif ratio > 1.2:
            return "Consider expanding capacity or increasing prices during peak periods"
        else:
            return "Occupancy levels are within target range"
    
    def _get_efficiency_recommendation(self, ratio: float) -> str:
        """Get recommendation for booking efficiency."""
        if ratio < 0.8:
            return "Investigate booking failures and improve system reliability"
        elif ratio >= 0.95:
            return "Excellent booking efficiency - maintain current processes"
        else:
            return "Good efficiency levels - minor optimizations possible"
    
    def _get_conflict_recommendation(self, conflict_rate: float) -> str:
        """Get recommendation for conflict rate."""
        if conflict_rate > 0.1:
            return "High conflict rate - implement buffer time optimization and capacity management"
        elif conflict_rate < 0.02:
            return "Very low conflicts - system running smoothly"
        else:
            return "Moderate conflicts - monitor and optimize buffer strategies"
    
    def _get_revenue_recommendation(self, ratio: float) -> str:
        """Get recommendation for revenue performance."""
        if ratio < 0.8:
            return "Revenue below target - review pricing strategy and occupancy optimization"
        elif ratio > 1.3:
            return "Strong revenue performance - consider reinvestment in capacity or amenities"
        else:
            return "Revenue performance is meeting expectations"
    
    async def _analyze_peak_hours(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Analyze peak usage hours."""
        try:
            # Group bookings by hour and count
            query = select(
                func.extract('hour', Booking.start_time).label('hour'),
                func.count(Booking.id).label('booking_count'),
                func.avg(func.extract('epoch', Booking.end_time - Booking.start_time) / 60).label('avg_duration')
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.start_time >= start_time,
                    Booking.start_time <= end_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            ).group_by(
                func.extract('hour', Booking.start_time)
            ).order_by(
                func.count(Booking.id).desc()
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            peak_hours = []
            for row in rows[:5]:  # Top 5 peak hours
                peak_hours.append({
                    "hour": int(row.hour),
                    "booking_count": row.booking_count,
                    "average_duration_minutes": round(float(row.avg_duration or 0), 2),
                    "time_display": f"{int(row.hour):02d}:00-{int(row.hour)+1:02d}:00"
                })
            
            return peak_hours
            
        except Exception as e:
            self.logger.error("Error analyzing peak hours", error=str(e))
            return []
    
    async def _analyze_booking_patterns(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Analyze booking patterns and trends."""
        try:
            # Analyze by day of week
            day_query = select(
                func.extract('dow', Booking.start_time).label('day_of_week'),
                func.count(Booking.id).label('booking_count')
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.start_time >= start_time,
                    Booking.start_time <= end_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            ).group_by(
                func.extract('dow', Booking.start_time)
            )
            
            day_result = await self.session.execute(day_query)
            day_rows = day_result.all()
            
            day_patterns = {}
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for row in day_rows:
                day_name = day_names[int(row.day_of_week)]
                day_patterns[day_name] = row.booking_count
            
            # Analyze by vehicle type
            vehicle_query = select(
                Booking.vehicle_type,
                func.count(Booking.id).label('booking_count'),
                func.avg(func.extract('epoch', Booking.end_time - Booking.start_time) / 60).label('avg_duration')
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Booking.start_time >= start_time,
                    Booking.start_time <= end_time,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.CHECKED_IN.value,
                        BookingStatus.COMPLETED.value
                    ])
                )
            ).group_by(Booking.vehicle_type)
            
            vehicle_result = await self.session.execute(vehicle_query)
            vehicle_rows = vehicle_result.all()
            
            vehicle_patterns = {}
            for row in vehicle_rows:
                vehicle_patterns[row.vehicle_type] = {
                    "booking_count": row.booking_count,
                    "average_duration_minutes": round(float(row.avg_duration or 0), 2)
                }
            
            return {
                "day_of_week_patterns": day_patterns,
                "vehicle_type_patterns": vehicle_patterns,
                "analysis_period_days": (end_time - start_time).days
            }
            
        except Exception as e:
            self.logger.error("Error analyzing booking patterns", error=str(e))
            return {}
    
    async def _analyze_revenue_performance(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Analyze revenue performance and trends."""
        try:
            # Revenue by day
            daily_revenue_query = select(
                func.date(Payment.created_at).label('date'),
                func.sum(Payment.amount).label('daily_revenue'),
                func.count(Payment.id).label('payment_count')
            ).join(
                Booking, Payment.booking_id == Booking.id
            ).where(
                and_(
                    Booking.lot_id == lot_id,
                    Payment.created_at >= start_time,
                    Payment.created_at <= end_time,
                    Payment.status == PaymentStatus.COMPLETED.value
                )
            ).group_by(
                func.date(Payment.created_at)
            ).order_by(
                func.date(Payment.created_at)
            )
            
            daily_result = await self.session.execute(daily_revenue_query)
            daily_rows = daily_result.all()
            
            daily_revenue = []
            total_revenue = Decimal('0.00')
            
            for row in daily_rows:
                revenue = row.daily_revenue or Decimal('0.00')
                total_revenue += revenue
                daily_revenue.append({
                    "date": row.date.isoformat(),
                    "revenue": float(revenue),
                    "payment_count": row.payment_count
                })
            
            # Calculate average daily revenue
            period_days = max((end_time - start_time).days, 1)
            avg_daily_revenue = total_revenue / period_days
            
            return {
                "total_revenue": float(total_revenue),
                "average_daily_revenue": float(avg_daily_revenue),
                "daily_breakdown": daily_revenue,
                "period_days": period_days
            }
            
        except Exception as e:
            self.logger.error("Error analyzing revenue performance", error=str(e))
            return {}
    
    async def _identify_optimization_opportunities(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Identify optimization opportunities."""
        opportunities = []
        
        try:
            # Check for low-utilization periods
            hourly_utilization = await self._get_hourly_utilization(lot_id, start_time, end_time)
            
            low_util_hours = [
                hour for hour, util in hourly_utilization.items() 
                if util < 0.3  # Less than 30% utilization
            ]
            
            if low_util_hours:
                opportunities.append({
                    "type": "low_utilization_periods",
                    "priority": "medium",
                    "description": f"Low utilization during hours: {', '.join(map(str, low_util_hours))}",
                    "recommendation": "Consider promotional pricing or marketing campaigns for these periods",
                    "potential_impact": "15-25% revenue increase"
                })
            
            # Check for high conflict periods
            conflict_rate = await self._calculate_conflict_rate(lot_id, start_time, end_time)
            if conflict_rate > 0.1:
                opportunities.append({
                    "type": "high_conflict_rate",
                    "priority": "high",
                    "description": f"Conflict rate of {conflict_rate:.1%} exceeds target of 5%",
                    "recommendation": "Implement dynamic buffer time and improve chunk allocation strategy",
                    "potential_impact": "Reduce conflicts by 60-80%"
                })
            
            # Check for revenue optimization
            revenue_per_hour = await self._calculate_revenue_per_hour(lot_id, start_time, end_time)
            if revenue_per_hour < self.benchmarks["revenue_per_hour"]:
                opportunities.append({
                    "type": "revenue_optimization",
                    "priority": "high",
                    "description": f"Revenue per hour ${revenue_per_hour:.2f} below target ${self.benchmarks['revenue_per_hour']:.2f}",
                    "recommendation": "Review pricing strategy and implement dynamic pricing",
                    "potential_impact": "20-40% revenue increase"
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Error identifying optimization opportunities", error=str(e))
            return []
    
    async def _get_hourly_utilization(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[int, float]:
        """Get utilization rate by hour of day."""
        # Simplified implementation - return mock data for now
        return {hour: 0.5 for hour in range(24)}  # 50% utilization placeholder
    
    def _get_default_time_window(self, period: AnalyticsPeriod) -> Tuple[datetime, datetime]:
        """Get default time window for analysis period."""
        end_time = datetime.now(timezone.utc)
        
        if period == AnalyticsPeriod.HOURLY:
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
        elif period == AnalyticsPeriod.DAILY:
            start_time = end_time - timedelta(days=7)   # Last 7 days
        elif period == AnalyticsPeriod.WEEKLY:
            start_time = end_time - timedelta(weeks=4)  # Last 4 weeks
        elif period == AnalyticsPeriod.MONTHLY:
            start_time = end_time - timedelta(days=90)  # Last 3 months
        else:  # YEARLY
            start_time = end_time - timedelta(days=365) # Last year
        
        return start_time, end_time
    
    def _calculate_report_confidence(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime,
        metrics: UtilizationMetrics
    ) -> float:
        """Calculate confidence level in the analytics report."""
        # Base confidence on data availability and consistency
        base_confidence = 0.8
        
        # Reduce confidence for short analysis periods
        period_hours = (end_time - start_time).total_seconds() / 3600
        if period_hours < 24:
            base_confidence -= 0.2
        elif period_hours < 72:
            base_confidence -= 0.1
        
        # Reduce confidence if metrics seem inconsistent
        if metrics.occupancy_rate > 0.95 and metrics.conflict_rate < 0.01:
            base_confidence -= 0.1  # Suspiciously perfect metrics
        
        return min(max(base_confidence, 0.1), 1.0)
    
    async def _get_total_slots(self, lot_id: UUID) -> int:
        """Get total number of slots in a parking lot."""
        query = select(func.count(ParkingSlot.id)).where(ParkingSlot.lot_id == lot_id)
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def _count_data_points(
        self,
        lot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count data points analyzed for confidence calculation."""
        booking_query = select(func.count(Booking.id)).where(
            and_(
                Booking.lot_id == lot_id,
                Booking.created_at >= start_time,
                Booking.created_at <= end_time
            )
        )
        
        result = await self.session.execute(booking_query)
        return result.scalar() or 0


# Factory function for dependency injection
def create_utilization_analytics(session: AsyncSession) -> UtilizationAnalytics:
    """Factory function to create UtilizationAnalytics instance."""
    return UtilizationAnalytics(session)
