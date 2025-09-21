"""Analytics API endpoints for admin dashboard."""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_async_session
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.utilization_analytics import UtilizationAnalytics, AnalyticsPeriod, UtilizationMetric
from app.services.booking import BookingService
from app.services.parking import ParkingService
from app.schemas.common import ApiResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_analytics_overview(
    start_date: Optional[date] = Query(None, description="Start date for analytics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analytics (YYYY-MM-DD)"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get comprehensive analytics overview for admin dashboard."""
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Convert to datetime with timezone
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        booking_service = BookingService(session)
        parking_service = ParkingService(session)
        
        # Get basic metrics
        total_lots = await parking_service.count(is_active=True)
        total_bookings = await booking_service.count_bookings_in_period(start_datetime, end_datetime)
        
        # Get utilization overview
        utilization_overview = await analytics_service.get_utilization_overview(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get revenue analytics
        revenue_data = await analytics_service.get_revenue_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            period=AnalyticsPeriod.DAILY,
            lot_id=lot_id
        )
        
        # Get booking patterns
        booking_patterns = await analytics_service.get_booking_patterns(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get peak hours analysis
        peak_hours = await analytics_service.get_peak_hours_analysis(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get vehicle type breakdown
        vehicle_breakdown = await analytics_service.get_vehicle_type_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        overview_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "summary": {
                "total_lots": total_lots,
                "total_bookings": total_bookings,
                "average_daily_bookings": round(total_bookings / ((end_date - start_date).days + 1), 2),
                "utilization_rate": utilization_overview.get("overall_utilization_rate", 0),
                "total_revenue": float(revenue_data.get("total_revenue", 0)),
                "average_daily_revenue": float(revenue_data.get("average_daily_revenue", 0))
            },
            "utilization": utilization_overview,
            "revenue": revenue_data,
            "booking_patterns": booking_patterns,
            "peak_hours": peak_hours,
            "vehicle_breakdown": vehicle_breakdown
        }
        
        logger.info(
            "Analytics overview generated",
            admin_id=current_admin.id,
            start_date=start_date,
            end_date=end_date,
            lot_id=lot_id
        )
        
        return ApiResponse(
            success=True,
            data=overview_data,
            message=f"Analytics overview for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get analytics overview", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics overview")


@router.get("/revenue", response_model=ApiResponse[Dict[str, Any]])
async def get_revenue_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Time period for grouping"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get detailed revenue analytics."""
    try:
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        revenue_data = await analytics_service.get_revenue_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            period=period,
            lot_id=lot_id
        )
        
        return ApiResponse(
            success=True,
            data=revenue_data,
            message=f"Revenue analytics for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get revenue analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue analytics")


@router.get("/utilization", response_model=ApiResponse[Dict[str, Any]])
async def get_utilization_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get space utilization analytics."""
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        utilization_data = await analytics_service.get_utilization_overview(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get detailed utilization by time periods
        hourly_utilization = await analytics_service.get_utilization_by_period(
            start_time=start_datetime,
            end_time=end_datetime,
            period=AnalyticsPeriod.HOURLY,
            lot_id=lot_id
        )
        
        daily_utilization = await analytics_service.get_utilization_by_period(
            start_time=start_datetime,
            end_time=end_datetime,
            period=AnalyticsPeriod.DAILY,
            lot_id=lot_id
        )
        
        utilization_data.update({
            "hourly_breakdown": hourly_utilization,
            "daily_breakdown": daily_utilization
        })
        
        return ApiResponse(
            success=True,
            data=utilization_data,
            message=f"Utilization analytics for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get utilization analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve utilization analytics")


@router.get("/occupancy", response_model=ApiResponse[Dict[str, Any]])
async def get_occupancy_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get occupancy patterns and heatmap data."""
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=7)  # Default to last week for occupancy
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        # Get peak hours analysis
        peak_hours = await analytics_service.get_peak_hours_analysis(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get occupancy heatmap data (hourly breakdown by day)
        occupancy_heatmap = await analytics_service.get_occupancy_heatmap(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get occupancy trends
        occupancy_trends = await analytics_service.get_utilization_by_period(
            start_time=start_datetime,
            end_time=end_datetime,
            period=AnalyticsPeriod.HOURLY,
            lot_id=lot_id
        )
        
        occupancy_data = {
            "peak_hours": peak_hours,
            "heatmap": occupancy_heatmap,
            "trends": occupancy_trends,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        return ApiResponse(
            success=True,
            data=occupancy_data,
            message=f"Occupancy analytics for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get occupancy analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve occupancy analytics")


@router.get("/booking-patterns", response_model=ApiResponse[Dict[str, Any]])
async def get_booking_patterns(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get booking pattern analytics."""
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        booking_patterns = await analytics_service.get_booking_patterns(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get additional pattern insights
        vehicle_analytics = await analytics_service.get_vehicle_type_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        duration_patterns = await analytics_service.get_booking_duration_analysis(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        pattern_data = {
            "booking_patterns": booking_patterns,
            "vehicle_analytics": vehicle_analytics,
            "duration_patterns": duration_patterns
        }
        
        return ApiResponse(
            success=True,
            data=pattern_data,
            message=f"Booking patterns for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get booking patterns", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve booking patterns")


@router.get("/performance", response_model=ApiResponse[Dict[str, Any]])
async def get_performance_metrics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get performance metrics and KPIs."""
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        # Get performance benchmarks
        performance_metrics = await analytics_service.get_performance_benchmarks(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Get efficiency metrics
        efficiency_metrics = await analytics_service.get_space_efficiency_metrics(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        # Combine metrics
        performance_data = {
            "performance_benchmarks": performance_metrics,
            "efficiency_metrics": efficiency_metrics,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            }
        }
        
        return ApiResponse(
            success=True,
            data=performance_data,
            message=f"Performance metrics for {start_date} to {end_date}"
        )
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/lots/{lot_id}/analytics", response_model=ApiResponse[Dict[str, Any]])
async def get_lot_specific_analytics(
    lot_id: str,
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get detailed analytics for a specific parking lot."""
    try:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        parking_service = ParkingService(session)
        
        # Get lot details
        lot = await parking_service.get_by_id(lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Parking lot not found")
        
        # Get comprehensive analytics for this lot
        utilization = await analytics_service.get_utilization_overview(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        revenue = await analytics_service.get_revenue_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            period=AnalyticsPeriod.DAILY,
            lot_id=lot_id
        )
        
        peak_hours = await analytics_service.get_peak_hours_analysis(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        vehicle_breakdown = await analytics_service.get_vehicle_type_analytics(
            start_time=start_datetime,
            end_time=end_datetime,
            lot_id=lot_id
        )
        
        lot_analytics = {
            "lot_info": {
                "id": lot.id,
                "name": lot.name,
                "address": lot.address,
                "total_car_slots": lot.total_car_slots,
                "total_bike_slots": lot.total_bike_slots,
                "total_slots": lot.total_car_slots + lot.total_bike_slots
            },
            "utilization": utilization,
            "revenue": revenue,
            "peak_hours": peak_hours,
            "vehicle_breakdown": vehicle_breakdown,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        return ApiResponse(
            success=True,
            data=lot_analytics,
            message=f"Analytics for {lot.name} from {start_date} to {end_date}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get lot-specific analytics", lot_id=lot_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve lot analytics")


@router.get("/reports/daily", response_model=ApiResponse[Dict[str, Any]])
async def get_daily_report(
    target_date: Optional[date] = Query(None, description="Target date for report (default: yesterday)"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get comprehensive daily report."""
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # Default to yesterday
        
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        analytics_service = UtilizationAnalytics(session)
        
        # Generate comprehensive daily report
        daily_report = await analytics_service.generate_daily_report(target_date)
        
        return ApiResponse(
            success=True,
            data=daily_report,
            message=f"Daily report for {target_date}"
        )
        
    except Exception as e:
        logger.error("Failed to generate daily report", target_date=target_date, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate daily report")
