"""Pricing service for dynamic pricing calculations."""

from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.repositories.pricing import PricingRuleRepository
from app.models.pricing import PricingRule, PricingRuleType
from app.models.parking import VehicleType
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
import structlog

logger = structlog.get_logger(__name__)


class PricingService(BaseService[PricingRule, PricingRuleRepository]):
    """Service for handling dynamic pricing operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pricing_repository = PricingRuleRepository(session)
        super().__init__(self.pricing_repository)
        self.logger = logger.bind(service="PricingService")
    
    async def calculate_booking_price(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate total price for a booking based on dynamic pricing rules."""
        try:
            # Validate input
            if start_time >= end_time:
                raise ValidationError("Start time must be before end time")
            
            # Calculate pricing using repository method
            pricing_result = await self.pricing_repository.calculate_pricing(
                lot_id, vehicle_type, start_time, end_time
            )
            
            # Add additional metadata
            pricing_result.update({
                "currency": "USD",
                "lot_id": str(lot_id),
                "vehicle_type": vehicle_type.value,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            })
            
            self.logger.info(
                "Calculated booking price",
                lot_id=lot_id,
                vehicle_type=vehicle_type.value,
                total_amount=pricing_result["total_amount"]
            )
            
            return pricing_result
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error("Failed to calculate booking price", error=str(e))
            raise BusinessLogicError("Failed to calculate pricing")
    
    async def get_pricing_preview(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        duration_hours: float
    ) -> Dict[str, Any]:
        """Get pricing preview for different time periods."""
        try:
            current_time = datetime.utcnow()
            
            # Calculate for current time
            end_time = current_time + timedelta(hours=duration_hours)
            current_pricing = await self.calculate_booking_price(
                lot_id, vehicle_type, current_time, end_time
            )
            
            # Calculate for peak hours (if applicable)
            peak_rules = await self.pricing_repository.get_peak_hour_rules(lot_id, vehicle_type)
            peak_pricing = None
            
            if peak_rules:
                # Use first peak rule for preview
                peak_rule = peak_rules[0]
                if peak_rule.start_time:
                    # Calculate for peak time today
                    peak_start = datetime.combine(current_time.date(), peak_rule.start_time)
                    if peak_start < current_time:
                        # Peak time has passed today, use tomorrow
                        peak_start = peak_start + timedelta(days=1)
                    
                    peak_end = peak_start + timedelta(hours=duration_hours)
                    peak_pricing = await self.calculate_booking_price(
                        lot_id, vehicle_type, peak_start, peak_end
                    )
            
            # Calculate for weekend (if applicable)
            weekend_rules = await self.pricing_repository.get_weekend_rules(lot_id, vehicle_type)
            weekend_pricing = None
            
            if weekend_rules:
                # Find next weekend
                days_until_weekend = (5 - current_time.weekday()) % 7  # Saturday
                if days_until_weekend == 0 and current_time.weekday() != 5:
                    days_until_weekend = 7
                
                weekend_start = current_time + timedelta(days=days_until_weekend)
                weekend_start = weekend_start.replace(hour=current_time.hour, minute=current_time.minute)
                weekend_end = weekend_start + timedelta(hours=duration_hours)
                
                weekend_pricing = await self.calculate_booking_price(
                    lot_id, vehicle_type, weekend_start, weekend_end
                )
            
            return {
                "duration_hours": duration_hours,
                "current_time": current_pricing,
                "peak_time": peak_pricing,
                "weekend_time": weekend_pricing,
                "currency": "USD"
            }
            
        except Exception as e:
            self.logger.error("Failed to get pricing preview", error=str(e))
            raise BusinessLogicError("Failed to get pricing preview")
    
    async def create_pricing_rule(
        self,
        lot_id: UUID,
        name: str,
        vehicle_type: VehicleType,
        rule_type: PricingRuleType,
        price_per_hour: float,
        multiplier: float = 1.0,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        days_of_week: Optional[List[str]] = None,
        priority: str = "normal",
        min_charge: Optional[float] = None,
        max_charge: Optional[float] = None
    ) -> PricingRule:
        """Create a new pricing rule."""
        try:
            # Validate pricing rule data
            await self._validate_pricing_rule_data(
                lot_id, rule_type, price_per_hour, multiplier, start_time, end_time, priority
            )
            
            rule_data = {
                "lot_id": lot_id,
                "name": name,
                "vehicle_type": vehicle_type.value,
                "rule_type": rule_type.value,
                "price_per_hour": Decimal(str(price_per_hour)),
                "multiplier": Decimal(str(multiplier)),
                "priority": priority
            }
            
            if start_time:
                rule_data["start_time"] = start_time
            if end_time:
                rule_data["end_time"] = end_time
            if days_of_week:
                rule_data["days_of_week"] = ",".join(days_of_week)
            if min_charge:
                rule_data["min_charge"] = Decimal(str(min_charge))
            if max_charge:
                rule_data["max_charge"] = Decimal(str(max_charge))
            
            rule = await self.pricing_repository.create(**rule_data)
            
            self.logger.info("Created pricing rule", rule_id=rule.id, lot_id=lot_id)
            return rule
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error("Failed to create pricing rule", error=str(e))
            raise BusinessLogicError("Failed to create pricing rule")
    
    async def update_pricing_rule(
        self,
        rule_id: UUID,
        **update_data
    ) -> PricingRule:
        """Update an existing pricing rule."""
        try:
            # Get existing rule
            existing_rule = await self.pricing_repository.get_by_id(rule_id)
            if not existing_rule:
                raise NotFoundError("Pricing rule not found")
            
            # Validate update data
            if "price_per_hour" in update_data:
                price_per_hour = update_data["price_per_hour"]
                if price_per_hour <= 0:
                    raise ValidationError("Price per hour must be positive")
                update_data["price_per_hour"] = Decimal(str(price_per_hour))
            
            if "multiplier" in update_data:
                multiplier = update_data["multiplier"]
                if multiplier <= 0:
                    raise ValidationError("Multiplier must be positive")
                update_data["multiplier"] = Decimal(str(multiplier))
            
            # Convert lists to comma-separated strings
            if "days_of_week" in update_data and isinstance(update_data["days_of_week"], list):
                update_data["days_of_week"] = ",".join(update_data["days_of_week"])
            
            updated_rule = await self.pricing_repository.update(rule_id, **update_data)
            
            self.logger.info("Updated pricing rule", rule_id=rule_id)
            return updated_rule
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Failed to update pricing rule", rule_id=rule_id, error=str(e))
            raise BusinessLogicError("Failed to update pricing rule")
    
    async def delete_pricing_rule(self, rule_id: UUID) -> bool:
        """Delete a pricing rule."""
        try:
            existing_rule = await self.pricing_repository.get_by_id(rule_id)
            if not existing_rule:
                raise NotFoundError("Pricing rule not found")
            
            deleted = await self.pricing_repository.delete(rule_id)
            
            if deleted:
                self.logger.info("Deleted pricing rule", rule_id=rule_id)
            
            return deleted
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error("Failed to delete pricing rule", rule_id=rule_id, error=str(e))
            raise BusinessLogicError("Failed to delete pricing rule")
    
    async def get_lot_pricing_rules(
        self,
        lot_id: UUID,
        vehicle_type: Optional[VehicleType] = None,
        is_active: Optional[bool] = None
    ) -> List[PricingRule]:
        """Get all pricing rules for a parking lot."""
        try:
            return await self.pricing_repository.get_rules_by_lot(lot_id, vehicle_type, is_active)
            
        except Exception as e:
            self.logger.error("Failed to get lot pricing rules", lot_id=lot_id, error=str(e))
            raise BusinessLogicError("Failed to get pricing rules")
    
    async def get_applicable_rules_for_time(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        check_time: datetime
    ) -> List[PricingRule]:
        """Get pricing rules applicable for a specific time."""
        try:
            return await self.pricing_repository.get_applicable_rules(lot_id, vehicle_type, check_time)
            
        except Exception as e:
            self.logger.error("Failed to get applicable rules", error=str(e))
            raise BusinessLogicError("Failed to get applicable rules")
    
    async def create_default_pricing_rules(self, lot_id: UUID) -> List[PricingRule]:
        """Create default pricing rules for a new parking lot."""
        try:
            return await self.pricing_repository.create_default_rules(lot_id)
            
        except Exception as e:
            self.logger.error("Failed to create default pricing rules", lot_id=lot_id, error=str(e))
            raise BusinessLogicError("Failed to create default pricing rules")
    
    async def get_pricing_summary(self, lot_id: UUID) -> Dict[str, Any]:
        """Get pricing summary for a parking lot."""
        try:
            return await self.pricing_repository.get_pricing_summary(lot_id)
            
        except Exception as e:
            self.logger.error("Failed to get pricing summary", lot_id=lot_id, error=str(e))
            raise BusinessLogicError("Failed to get pricing summary")
    
    async def validate_pricing_configuration(self, lot_id: UUID) -> Dict[str, Any]:
        """Validate pricing configuration for a lot."""
        try:
            rules = await self.pricing_repository.get_rules_by_lot(lot_id, is_active=True)
            
            validation_result = {
                "is_valid": True,
                "issues": [],
                "recommendations": []
            }
            
            # Check if there are base rules for each vehicle type
            vehicle_types = [VehicleType.CAR, VehicleType.BIKE]
            for vehicle_type in vehicle_types:
                vehicle_rules = [r for r in rules if r.vehicle_type == vehicle_type.value]
                if not vehicle_rules:
                    validation_result["issues"].append(
                        f"No pricing rules defined for {vehicle_type.value}"
                    )
                    validation_result["is_valid"] = False
            
            # Check for overlapping time-based rules with same priority
            time_based_rules = [r for r in rules if r.rule_type == PricingRuleType.TIME_BASED.value]
            for i, rule1 in enumerate(time_based_rules):
                for rule2 in time_based_rules[i+1:]:
                    if (rule1.vehicle_type == rule2.vehicle_type and 
                        rule1.priority == rule2.priority and
                        self._rules_overlap(rule1, rule2)):
                        validation_result["issues"].append(
                            f"Overlapping rules with same priority: {rule1.name} and {rule2.name}"
                        )
            
            # Recommendations
            if not any(r.rule_type == PricingRuleType.TIME_BASED.value and r.priority == "high" 
                      for r in rules):
                validation_result["recommendations"].append(
                    "Consider adding peak hour pricing rules for increased revenue"
                )
            
            return validation_result
            
        except Exception as e:
            self.logger.error("Failed to validate pricing configuration", error=str(e))
            raise BusinessLogicError("Failed to validate pricing configuration")
    
    async def _validate_pricing_rule_data(
        self,
        lot_id: UUID,
        rule_type: PricingRuleType,
        price_per_hour: float,
        multiplier: float,
        start_time: Optional[time],
        end_time: Optional[time],
        priority: str
    ) -> None:
        """Validate pricing rule creation data."""
        if price_per_hour <= 0:
            raise ValidationError("Price per hour must be positive")
        
        if multiplier <= 0:
            raise ValidationError("Multiplier must be positive")
        
        if priority not in ["high", "normal", "low"]:
            raise ValidationError("Priority must be 'high', 'normal', or 'low'")
        
        if rule_type == PricingRuleType.TIME_BASED and (not start_time or not end_time):
            raise ValidationError("Time-based rules require start_time and end_time")
    
    def _rules_overlap(self, rule1: PricingRule, rule2: PricingRule) -> bool:
        """Check if two time-based rules overlap."""
        if not all([rule1.start_time, rule1.end_time, rule2.start_time, rule2.end_time]):
            return False
        
        # Handle overnight rules
        if rule1.start_time > rule1.end_time or rule2.start_time > rule2.end_time:
            # Complex logic for overnight rules - simplified for now
            return True
        
        # Normal rules within same day
        return not (rule1.end_time <= rule2.start_time or rule1.start_time >= rule2.end_time)
    
    def _get_entity_name(self) -> str:
        """Get entity name for base service."""
        return "PricingRule"
