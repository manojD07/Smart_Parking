"""Pricing rule repository for dynamic pricing operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, time, timedelta

from app.repositories.base import BaseRepository
from app.models.pricing import PricingRule, PricingRuleType
from app.models.parking import VehicleType


class PricingRuleRepository(BaseRepository[PricingRule]):
    """Repository for PricingRule model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PricingRule)
    
    async def get_applicable_rules(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType, 
        check_time: datetime
    ) -> List[PricingRule]:
        """Get pricing rules applicable for given lot, vehicle type, and time."""
        try:
            query = (
                select(PricingRule)
                .where(
                    and_(
                        PricingRule.lot_id == lot_id,
                        PricingRule.vehicle_type == vehicle_type.value,
                        PricingRule.is_active == True
                    )
                )
                .order_by(PricingRule.priority.desc(), PricingRule.created_at.asc())
            )
            
            result = await self.session.execute(query)
            all_rules = list(result.scalars().all())
            
            # Filter rules that apply to the given time
            applicable_rules = []
            for rule in all_rules:
                if rule.applies_to_time(check_time):
                    applicable_rules.append(rule)
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error("Failed to get applicable rules", error=str(e))
            raise
    
    async def get_rules_by_lot(
        self, 
        lot_id: UUID, 
        vehicle_type: Optional[VehicleType] = None,
        is_active: Optional[bool] = None
    ) -> List[PricingRule]:
        """Get all pricing rules for a parking lot."""
        try:
            query = select(PricingRule).where(PricingRule.lot_id == lot_id)
            
            if vehicle_type:
                query = query.where(PricingRule.vehicle_type == vehicle_type.value)
            
            if is_active is not None:
                query = query.where(PricingRule.is_active == is_active)
            
            query = query.order_by(PricingRule.priority.desc(), PricingRule.start_time.asc())
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get rules by lot", lot_id=lot_id, error=str(e))
            raise
    
    async def get_time_based_rules(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: time,
        end_time: time
    ) -> List[PricingRule]:
        """Get time-based pricing rules that overlap with given time range."""
        try:
            query = (
                select(PricingRule)
                .where(
                    and_(
                        PricingRule.lot_id == lot_id,
                        PricingRule.vehicle_type == vehicle_type.value,
                        PricingRule.rule_type == PricingRuleType.TIME_BASED.value,
                        PricingRule.is_active == True
                    )
                )
            )
            
            result = await self.session.execute(query)
            all_rules = list(result.scalars().all())
            
            # Filter rules that overlap with the time range
            overlapping_rules = []
            for rule in all_rules:
                if rule.start_time and rule.end_time:
                    # Handle overnight rules
                    if rule.start_time > rule.end_time:
                        # Rule spans midnight
                        if (start_time >= rule.start_time or end_time <= rule.end_time or
                            start_time <= rule.end_time or end_time >= rule.start_time):
                            overlapping_rules.append(rule)
                    else:
                        # Normal rule within same day
                        if not (end_time <= rule.start_time or start_time >= rule.end_time):
                            overlapping_rules.append(rule)
            
            return sorted(overlapping_rules, key=lambda r: (r.priority, r.start_time))
            
        except Exception as e:
            self.logger.error("Failed to get time-based rules", error=str(e))
            raise
    
    async def get_peak_hour_rules(self, lot_id: UUID, vehicle_type: VehicleType) -> List[PricingRule]:
        """Get peak hour pricing rules."""
        try:
            query = (
                select(PricingRule)
                .where(
                    and_(
                        PricingRule.lot_id == lot_id,
                        PricingRule.vehicle_type == vehicle_type.value,
                        PricingRule.rule_type == PricingRuleType.TIME_BASED.value,
                        PricingRule.priority == "high",
                        PricingRule.is_active == True
                    )
                )
                .order_by(PricingRule.start_time.asc())
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get peak hour rules", error=str(e))
            raise
    
    async def get_weekend_rules(self, lot_id: UUID, vehicle_type: VehicleType) -> List[PricingRule]:
        """Get weekend pricing rules."""
        try:
            query = (
                select(PricingRule)
                .where(
                    and_(
                        PricingRule.lot_id == lot_id,
                        PricingRule.vehicle_type == vehicle_type.value,
                        PricingRule.rule_type == PricingRuleType.DAY_BASED.value,
                        PricingRule.days_of_week.contains("saturday"),
                        PricingRule.is_active == True
                    )
                )
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get weekend rules", error=str(e))
            raise
    
    async def create_default_rules(self, lot_id: UUID) -> List[PricingRule]:
        """Create default pricing rules for a parking lot."""
        try:
            default_rules = []
            
            # Create base pricing rules for each vehicle type
            for vehicle_type in [VehicleType.CAR, VehicleType.BIKE]:
                # Base rate rule
                base_rule = await self.create(
                    lot_id=lot_id,
                    name=f"Base Rate - {vehicle_type.value.title()}",
                    vehicle_type=vehicle_type.value,
                    rule_type=PricingRuleType.TIME_BASED.value,
                    start_time=time(0, 0),
                    end_time=time(23, 59),
                    price_per_hour=5.0 if vehicle_type == VehicleType.CAR else 2.0,
                    multiplier=1.0,
                    priority="normal"
                )
                default_rules.append(base_rule)
                
                # Peak hour rule (6 PM - 10 PM)
                peak_rule = await self.create(
                    lot_id=lot_id,
                    name=f"Peak Hours - {vehicle_type.value.title()}",
                    vehicle_type=vehicle_type.value,
                    rule_type=PricingRuleType.TIME_BASED.value,
                    start_time=time(18, 0),
                    end_time=time(22, 0),
                    price_per_hour=5.0 if vehicle_type == VehicleType.CAR else 2.0,
                    multiplier=1.5,
                    priority="high"
                )
                default_rules.append(peak_rule)
                
                # Weekend rule
                weekend_rule = await self.create(
                    lot_id=lot_id,
                    name=f"Weekend Premium - {vehicle_type.value.title()}",
                    vehicle_type=vehicle_type.value,
                    rule_type=PricingRuleType.DAY_BASED.value,
                    days_of_week="saturday,sunday",
                    price_per_hour=5.0 if vehicle_type == VehicleType.CAR else 2.0,
                    multiplier=1.2,
                    priority="normal"
                )
                default_rules.append(weekend_rule)
            
            self.logger.info("Created default pricing rules", lot_id=lot_id, count=len(default_rules))
            return default_rules
            
        except Exception as e:
            self.logger.error("Failed to create default rules", lot_id=lot_id, error=str(e))
            raise
    
    async def calculate_pricing(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate pricing for a booking based on applicable rules."""
        try:
            total_amount = 0.0
            duration_hours = (end_time - start_time).total_seconds() / 3600
            
            # Get all applicable rules for the time period
            current_time = start_time
            pricing_breakdown = []
            
            while current_time < end_time:
                # Find applicable rules for current time
                applicable_rules = await self.get_applicable_rules(lot_id, vehicle_type, current_time)
                
                if not applicable_rules:
                    # No rules found, use default pricing
                    default_rate = 5.0 if vehicle_type == VehicleType.CAR else 2.0
                    remaining_hours = (end_time - current_time).total_seconds() / 3600
                    amount = default_rate * remaining_hours
                    total_amount += amount
                    
                    pricing_breakdown.append({
                        'rule_name': 'Default Rate',
                        'start_time': current_time,
                        'end_time': end_time,
                        'duration_hours': remaining_hours,
                        'rate_per_hour': default_rate,
                        'amount': amount
                    })
                    break
                
                # Use the highest priority rule
                rule = applicable_rules[0]
                
                # Calculate how long this rule applies
                if rule.rule_type == PricingRuleType.TIME_BASED.value and rule.start_time and rule.end_time:
                    # Calculate rule end time for current day
                    rule_end = datetime.combine(current_time.date(), rule.end_time)
                    if rule.start_time > rule.end_time:
                        # Overnight rule, extends to next day
                        if current_time.time() >= rule.start_time:
                            rule_end = datetime.combine(current_time.date() + timedelta(days=1), rule.end_time)
                    
                    segment_end = min(end_time, rule_end)
                else:
                    # Non-time-based rule applies for remaining duration
                    segment_end = end_time
                
                segment_hours = (segment_end - current_time).total_seconds() / 3600
                segment_amount = rule.calculate_charge(segment_hours)
                total_amount += segment_amount
                
                pricing_breakdown.append({
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'start_time': current_time,
                    'end_time': segment_end,
                    'duration_hours': segment_hours,
                    'rate_per_hour': rule.effective_price,
                    'multiplier': float(rule.multiplier),
                    'amount': segment_amount
                })
                
                current_time = segment_end
            
            return {
                'total_amount': round(total_amount, 2),
                'duration_hours': duration_hours,
                'average_rate': round(total_amount / duration_hours, 2) if duration_hours > 0 else 0,
                'pricing_breakdown': pricing_breakdown
            }
            
        except Exception as e:
            self.logger.error("Failed to calculate pricing", error=str(e))
            raise
    
    async def get_pricing_summary(self, lot_id: UUID) -> Dict[str, Any]:
        """Get a summary of all pricing rules for a lot."""
        try:
            rules = await self.get_rules_by_lot(lot_id, is_active=True)
            
            summary = {
                'total_rules': len(rules),
                'rules_by_type': {},
                'rules_by_vehicle': {},
                'rules_by_priority': {}
            }
            
            for rule in rules:
                # Count by type
                if rule.rule_type not in summary['rules_by_type']:
                    summary['rules_by_type'][rule.rule_type] = 0
                summary['rules_by_type'][rule.rule_type] += 1
                
                # Count by vehicle type
                if rule.vehicle_type not in summary['rules_by_vehicle']:
                    summary['rules_by_vehicle'][rule.vehicle_type] = 0
                summary['rules_by_vehicle'][rule.vehicle_type] += 1
                
                # Count by priority
                if rule.priority not in summary['rules_by_priority']:
                    summary['rules_by_priority'][rule.priority] = 0
                summary['rules_by_priority'][rule.priority] += 1
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to get pricing summary", lot_id=lot_id, error=str(e))
            raise
    
    async def deactivate_expired_rules(self) -> int:
        """Deactivate pricing rules that have expired."""
        try:
            current_date = datetime.utcnow().date()
            
            # Find rules that have expired
            query = (
                select(PricingRule)
                .where(
                    and_(
                        PricingRule.is_active == True,
                        PricingRule.valid_until.is_not(None),
                        PricingRule.valid_until < current_date
                    )
                )
            )
            
            result = await self.session.execute(query)
            expired_rules = list(result.scalars().all())
            
            # Deactivate expired rules
            deactivated_count = 0
            for rule in expired_rules:
                await self.update(rule.id, is_active=False)
                deactivated_count += 1
            
            if deactivated_count > 0:
                self.logger.info("Deactivated expired pricing rules", count=deactivated_count)
            
            return deactivated_count
            
        except Exception as e:
            self.logger.error("Failed to deactivate expired rules", error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for pricing rule queries."""
        return query.options(joinedload(PricingRule.lot))
