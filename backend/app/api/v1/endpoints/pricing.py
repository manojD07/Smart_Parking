"""Pricing rule management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import time
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.pricing import PricingService
from app.schemas.pricing import (
    PricingRuleResponse,
    PricingRuleUpdate,
    PricingRuleListResponse,
    PricingSummaryResponse,
    PricingValidationResponse,
    PricingPreviewMultiResponse,
    BulkRuleUpdateRequest,
    RuleDuplicationRequest,
    DefaultRulesResponse
)
from app.schemas.parking import PricingRuleCreate
from app.schemas.common import SuccessResponse
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.models.parking import VehicleType
from app.models.pricing import PricingRuleType
from app.core.exceptions import create_http_exception, BaseApplicationError
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


# Core CRUD Operations

@router.get("/admin/lots/{lot_id}/rules", response_model=PricingRuleListResponse)
async def get_lot_pricing_rules(
    lot_id: UUID,
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all pricing rules for a parking lot (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        # Convert string to enum if provided
        vehicle_type_enum = VehicleType(vehicle_type) if vehicle_type else None
        
        # Get rules with filters
        rules = await pricing_service.get_lot_pricing_rules(
            lot_id=lot_id,
            vehicle_type=vehicle_type_enum,
            is_active=is_active
        )
        
        # Apply additional filters
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        
        # Apply pagination
        total = len(rules)
        paginated_rules = rules[skip:skip + limit]
        
        # Generate summary statistics
        summary = {
            "total_rules": total,
            "active_rules": len([r for r in rules if r.is_active]),
            "inactive_rules": len([r for r in rules if not r.is_active]),
            "rule_types": {
                "time_based": len([r for r in rules if r.rule_type == "time_based"]),
                "day_based": len([r for r in rules if r.rule_type == "day_based"]),
                "seasonal": len([r for r in rules if r.rule_type == "seasonal"]),
                "demand_based": len([r for r in rules if r.rule_type == "demand_based"])
            },
            "vehicle_types": {
                "car": len([r for r in rules if r.vehicle_type == "car"]),
                "bike": len([r for r in rules if r.vehicle_type == "bike"])
            }
        }
        
        return PricingRuleListResponse(
            rules=[PricingRuleResponse.from_orm(rule) for rule in paginated_rules],
            total=total,
            summary=summary
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/admin/rules", response_model=PricingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    rule_data: PricingRuleCreate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new pricing rule (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        # Convert enums
        vehicle_type = VehicleType(rule_data.vehicle_type)
        rule_type = PricingRuleType(rule_data.rule_type)
        
        rule = await pricing_service.create_pricing_rule(
            lot_id=rule_data.lot_id,
            name=rule_data.name,
            vehicle_type=vehicle_type,
            rule_type=rule_type,
            price_per_hour=rule_data.price_per_hour,
            multiplier=rule_data.multiplier,
            start_time=rule_data.start_time,
            end_time=rule_data.end_time,
            days_of_week=rule_data.days_of_week,
            priority=rule_data.priority,
            min_charge=rule_data.min_charge,
            max_charge=rule_data.max_charge
        )
        
        return PricingRuleResponse.from_orm(rule)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/rules/{rule_id}", response_model=PricingRuleResponse)
async def get_pricing_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific pricing rule (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        rule = await pricing_service.get_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pricing rule not found"
            )
        
        return PricingRuleResponse.from_orm(rule)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/admin/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: UUID,
    rule_data: PricingRuleUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a pricing rule (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        # Convert update data to dict, excluding None values
        update_data = rule_data.dict(exclude_unset=True)
        
        rule = await pricing_service.update_pricing_rule(rule_id, **update_data)
        
        return PricingRuleResponse.from_orm(rule)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.delete("/admin/rules/{rule_id}", response_model=SuccessResponse)
async def delete_pricing_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a pricing rule (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        success = await pricing_service.delete_pricing_rule(rule_id)
        
        if success:
            return SuccessResponse(message="Pricing rule deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete pricing rule"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/admin/rules/{rule_id}/toggle", response_model=PricingRuleResponse)
async def toggle_pricing_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Toggle pricing rule active status (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        # Get current rule
        rule = await pricing_service.get_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pricing rule not found"
            )
        
        # Toggle active status
        updated_rule = await pricing_service.update_pricing_rule(
            rule_id, 
            is_active=not rule.is_active
        )
        
        return PricingRuleResponse.from_orm(updated_rule)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Analytics and Management

@router.get("/admin/lots/{lot_id}/summary", response_model=PricingSummaryResponse)
async def get_pricing_summary(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get pricing summary and analytics for a parking lot (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        summary_data = await pricing_service.get_pricing_summary(lot_id)
        
        return PricingSummaryResponse(**summary_data)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/lots/{lot_id}/validation", response_model=PricingValidationResponse)
async def validate_pricing_configuration(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Validate pricing configuration for a parking lot (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        validation_result = await pricing_service.validate_pricing_configuration(lot_id)
        
        return PricingValidationResponse(**validation_result)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/lots/{lot_id}/preview", response_model=PricingPreviewMultiResponse)
async def get_pricing_preview_scenarios(
    lot_id: UUID,
    vehicle_type: str = Query(..., description="Vehicle type (car/bike)"),
    duration_hours: float = Query(2.0, gt=0, le=24, description="Duration in hours"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get pricing preview for different scenarios (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        vehicle_type_enum = VehicleType(vehicle_type)
        preview_data = await pricing_service.get_pricing_preview(
            lot_id, vehicle_type_enum, duration_hours
        )
        
        # Transform to multi-scenario response
        scenarios = {}
        if "current_time" in preview_data:
            scenarios["current"] = preview_data["current_time"]
        if "peak_time" in preview_data:
            scenarios["peak"] = preview_data["peak_time"]
        if "weekend_time" in preview_data:
            scenarios["weekend"] = preview_data["weekend_time"]
        
        return PricingPreviewMultiResponse(
            lot_id=lot_id,
            vehicle_type=vehicle_type,
            scenarios=scenarios,
            recommendations={
                "best_time": "off_peak_weekday",
                "potential_savings": 0.0
            }
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Advanced Operations

@router.post("/admin/lots/{lot_id}/default-rules", response_model=DefaultRulesResponse)
async def create_default_rules(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create default pricing rules for a parking lot (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        rules = await pricing_service.create_default_pricing_rules(lot_id)
        
        return DefaultRulesResponse(
            created_rules=len(rules),
            rules=[PricingRuleResponse.from_orm(rule) for rule in rules],
            message=f"Successfully created {len(rules)} default pricing rules"
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/admin/rules/bulk-update", response_model=SuccessResponse)
async def bulk_update_pricing_rules(
    bulk_request: BulkRuleUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Bulk update multiple pricing rules (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        update_data = bulk_request.updates.dict(exclude_unset=True)
        updated_count = 0
        
        for rule_id in bulk_request.rule_ids:
            try:
                await pricing_service.update_pricing_rule(rule_id, **update_data)
                updated_count += 1
            except Exception as e:
                logger.warning("Failed to update rule in bulk operation", rule_id=rule_id, error=str(e))
        
        return SuccessResponse(
            message=f"Successfully updated {updated_count} of {len(bulk_request.rule_ids)} pricing rules"
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/admin/rules/{rule_id}/duplicate", response_model=DefaultRulesResponse)
async def duplicate_pricing_rule(
    rule_id: UUID,
    duplication_request: RuleDuplicationRequest,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Duplicate a pricing rule to other parking lots (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        # Get source rule
        source_rule = await pricing_service.get_by_id(rule_id)
        if not source_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source pricing rule not found"
            )
        
        created_rules = []
        
        for target_lot_id in duplication_request.target_lot_ids:
            try:
                # Create duplicated rule
                new_rule = await pricing_service.create_pricing_rule(
                    lot_id=target_lot_id,
                    name=f"{duplication_request.name_prefix}{source_rule.name}",
                    vehicle_type=VehicleType(source_rule.vehicle_type),
                    rule_type=PricingRuleType(source_rule.rule_type),
                    price_per_hour=float(source_rule.price_per_hour),
                    multiplier=float(source_rule.multiplier),
                    start_time=source_rule.start_time,
                    end_time=source_rule.end_time,
                    days_of_week=source_rule.days_list if source_rule.days_list else None,
                    priority=source_rule.priority,
                    min_charge=float(source_rule.min_charge) if source_rule.min_charge else None,
                    max_charge=float(source_rule.max_charge) if source_rule.max_charge else None
                )
                created_rules.append(new_rule)
                
            except Exception as e:
                logger.warning("Failed to duplicate rule to lot", target_lot_id=target_lot_id, error=str(e))
        
        return DefaultRulesResponse(
            created_rules=len(created_rules),
            rules=[PricingRuleResponse.from_orm(rule) for rule in created_rules],
            message=f"Successfully duplicated rule to {len(created_rules)} parking lots"
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Analytics and Validation

@router.get("/admin/lots/{lot_id}/pricing-summary", response_model=PricingSummaryResponse)
async def get_detailed_pricing_summary(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get detailed pricing summary and analytics (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        summary_data = await pricing_service.get_pricing_summary(lot_id)
        
        return PricingSummaryResponse(**summary_data)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/lots/{lot_id}/pricing-validation", response_model=PricingValidationResponse)
async def validate_lot_pricing(
    lot_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Validate pricing configuration and get recommendations (admin only)."""
    try:
        pricing_service = PricingService(session)
        
        validation_result = await pricing_service.validate_pricing_configuration(lot_id)
        
        return PricingValidationResponse(**validation_result)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/admin/lots/{lot_id}/pricing-preview", response_model=PricingPreviewMultiResponse)
async def get_admin_pricing_preview(
    lot_id: UUID,
    vehicle_type: str = Query(..., description="Vehicle type (car/bike)"),
    duration_hours: float = Query(2.0, gt=0, le=24, description="Duration in hours"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get comprehensive pricing preview for admin analysis."""
    try:
        pricing_service = PricingService(session)
        
        vehicle_type_enum = VehicleType(vehicle_type)
        preview_data = await pricing_service.get_pricing_preview(
            lot_id, vehicle_type_enum, duration_hours
        )
        
        # Convert to structured response
        scenarios = {}
        recommendations = {"best_time": "off_peak", "potential_savings": 0.0}
        
        if "current_time" in preview_data and preview_data["current_time"]:
            scenarios["current"] = preview_data["current_time"]
        
        if "peak_time" in preview_data and preview_data["peak_time"]:
            scenarios["peak"] = preview_data["peak_time"]
            
        if "weekend_time" in preview_data and preview_data["weekend_time"]:
            scenarios["weekend"] = preview_data["weekend_time"]
        
        # Calculate recommendations
        if scenarios:
            min_price = min(s.get("total_amount", float('inf')) for s in scenarios.values())
            max_price = max(s.get("total_amount", 0) for s in scenarios.values())
            recommendations["potential_savings"] = max_price - min_price
        
        return PricingPreviewMultiResponse(
            lot_id=lot_id,
            vehicle_type=vehicle_type,
            scenarios=scenarios,
            recommendations=recommendations
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)
