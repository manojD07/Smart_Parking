"""Pricing rule schemas for API responses and requests."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import time, datetime
from decimal import Decimal


class PricingRuleResponse(BaseModel):
    """Pricing rule response schema."""
    
    id: UUID = Field(..., description="Pricing rule ID")
    lot_id: UUID = Field(..., description="Parking lot ID")
    name: str = Field(..., description="Rule name")
    vehicle_type: str = Field(..., description="Vehicle type")
    rule_type: str = Field(..., description="Rule type")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    days_of_week: Optional[str] = Field(None, description="Days of week (comma-separated)")
    price_per_hour: float = Field(..., description="Base price per hour")
    multiplier: float = Field(..., description="Price multiplier")
    effective_price: float = Field(..., description="Effective price (base * multiplier)")
    min_charge: Optional[float] = Field(None, description="Minimum charge")
    max_charge: Optional[float] = Field(None, description="Maximum charge")
    is_active: bool = Field(..., description="Whether rule is active")
    priority: str = Field(..., description="Rule priority")
    valid_from: Optional[time] = Field(None, description="Valid from time")
    valid_until: Optional[time] = Field(None, description="Valid until time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Computed fields
    days_list: List[str] = Field(default_factory=list, description="Days of week as list")
    
    @classmethod
    def from_orm(cls, pricing_rule):
        """Create response from ORM model."""
        return cls(
            id=pricing_rule.id,
            lot_id=pricing_rule.lot_id,
            name=pricing_rule.name,
            vehicle_type=pricing_rule.vehicle_type,
            rule_type=pricing_rule.rule_type,
            start_time=pricing_rule.start_time,
            end_time=pricing_rule.end_time,
            days_of_week=pricing_rule.days_of_week,
            price_per_hour=float(pricing_rule.price_per_hour),
            multiplier=float(pricing_rule.multiplier),
            effective_price=pricing_rule.effective_price,
            min_charge=float(pricing_rule.min_charge) if pricing_rule.min_charge else None,
            max_charge=float(pricing_rule.max_charge) if pricing_rule.max_charge else None,
            is_active=pricing_rule.is_active,
            priority=pricing_rule.priority,
            valid_from=pricing_rule.valid_from,
            valid_until=pricing_rule.valid_until,
            created_at=pricing_rule.created_at,
            updated_at=pricing_rule.updated_at,
            days_list=pricing_rule.days_list
        )

    class Config:
        from_attributes = True
        json_encoders = {
            time: lambda v: v.strftime('%H:%M:%S') if v else None,
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PricingRuleUpdate(BaseModel):
    """Pricing rule update schema."""
    
    name: Optional[str] = Field(None, min_length=1, description="Rule name")
    vehicle_type: Optional[str] = Field(None, description="Vehicle type")
    rule_type: Optional[str] = Field(None, description="Rule type")
    start_time: Optional[time] = Field(None, description="Start time")
    end_time: Optional[time] = Field(None, description="End time")
    days_of_week: Optional[List[str]] = Field(None, description="Days of week")
    price_per_hour: Optional[float] = Field(None, gt=0, description="Price per hour")
    multiplier: Optional[float] = Field(None, gt=0, description="Price multiplier")
    min_charge: Optional[float] = Field(None, ge=0, description="Minimum charge")
    max_charge: Optional[float] = Field(None, ge=0, description="Maximum charge")
    is_active: Optional[bool] = Field(None, description="Whether rule is active")
    priority: Optional[str] = Field(None, description="Rule priority")
    valid_from: Optional[time] = Field(None, description="Valid from time")
    valid_until: Optional[time] = Field(None, description="Valid until time")


class PricingRuleListResponse(BaseModel):
    """Pricing rules list response schema."""
    
    rules: List[PricingRuleResponse] = Field(..., description="List of pricing rules")
    total: int = Field(..., description="Total number of rules")
    summary: Dict[str, Any] = Field(..., description="Rules summary statistics")


class PricingSummaryResponse(BaseModel):
    """Pricing summary response schema."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    total_rules: int = Field(..., description="Total number of rules")
    active_rules: int = Field(..., description="Number of active rules")
    inactive_rules: int = Field(..., description="Number of inactive rules")
    
    rule_breakdown: Dict[str, int] = Field(..., description="Rules by type")
    vehicle_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Rules by vehicle type")
    pricing_coverage: Dict[str, float] = Field(..., description="Time coverage percentages")
    
    # Analytics
    average_rates: Dict[str, float] = Field(..., description="Average rates by vehicle type")
    peak_rates: Dict[str, float] = Field(..., description="Peak rates by vehicle type")
    revenue_potential: Dict[str, float] = Field(..., description="Estimated revenue potential")


class PricingValidationResponse(BaseModel):
    """Pricing validation response schema."""
    
    is_valid: bool = Field(..., description="Whether configuration is valid")
    issues: List[str] = Field(..., description="Validation issues found")
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    conflicts: List[Dict[str, Any]] = Field(..., description="Rule conflicts")
    coverage_gaps: List[str] = Field(..., description="Time periods without rules")


class PricingPreviewScenario(BaseModel):
    """Pricing preview scenario."""
    
    scenario_name: str = Field(..., description="Scenario name")
    total_amount: float = Field(..., description="Total cost")
    duration_hours: float = Field(..., description="Duration in hours")
    average_rate: float = Field(..., description="Average rate per hour")
    applicable_rules: List[str] = Field(..., description="Rules that apply")
    breakdown: List[Dict[str, Any]] = Field(..., description="Detailed breakdown")


class PricingPreviewMultiResponse(BaseModel):
    """Multi-scenario pricing preview response."""
    
    lot_id: UUID = Field(..., description="Parking lot ID")
    vehicle_type: str = Field(..., description="Vehicle type")
    scenarios: Dict[str, PricingPreviewScenario] = Field(..., description="Different pricing scenarios")
    recommendations: Dict[str, Any] = Field(..., description="Recommendations for users")


class BulkRuleUpdateRequest(BaseModel):
    """Bulk rule update request schema."""
    
    rule_ids: List[UUID] = Field(..., description="List of rule IDs to update")
    updates: PricingRuleUpdate = Field(..., description="Updates to apply")


class RuleDuplicationRequest(BaseModel):
    """Rule duplication request schema."""
    
    source_rule_id: UUID = Field(..., description="Rule to duplicate")
    target_lot_ids: List[UUID] = Field(..., description="Target parking lots")
    name_prefix: Optional[str] = Field("Copy of ", description="Prefix for duplicated rule names")
    
    
class DefaultRulesResponse(BaseModel):
    """Default rules creation response."""
    
    created_rules: int = Field(..., description="Number of rules created")
    rules: List[PricingRuleResponse] = Field(..., description="Created rules")
    message: str = Field(..., description="Success message")
