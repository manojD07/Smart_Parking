"""Booking service for handling parking reservations."""

from datetime import datetime, timedelta, timezone
from app.core.timezone import now as ist_now, to_ist, ensure_ist
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService, TransactionalService
from app.repositories.booking import BookingRepository, SlotAllocationRepository
from app.repositories.parking import ParkingLotRepository, ParkingSlotRepository
from app.repositories.user import UserRepository
from app.services.pricing import PricingService
from app.core.config import settings
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    BookingConflictError,
    InsufficientSlotsError,
    BookingNotCancellableError,
    InvalidTimeRangeError,
    ParkingLotNotActiveError,
    UserNotActiveError,
    BusinessLogicError
)
from app.models.booking import Booking, BookingStatus, SlotAllocation, AllocationType
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)


class BookingService(BaseService[Booking, BookingRepository], TransactionalService):
    """Service for handling parking booking operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.slot_allocation_repository = SlotAllocationRepository(session)
        self.parking_lot_repository = ParkingLotRepository(session)
        self.parking_slot_repository = ParkingSlotRepository(session)
        self.user_repository = UserRepository(session)
        self.pricing_service = PricingService(session)
        
        super().__init__(self.booking_repository)
        TransactionalService.__init__(self, session)
        
        self.logger = logger.bind(service="BookingService")
    
    async def create_booking(
        self,
        user_id: UUID,
        lot_id: UUID,
        vehicle_type: VehicleType,
        vehicle_number: str,
        start_time: datetime,
        end_time: datetime
    ) -> Booking:
        """Create a new parking booking."""
        try:
            # Ensure datetimes are timezone-aware in IST before processing
            start_time = to_ist(start_time) if start_time.tzinfo else ensure_ist(start_time)
            end_time = to_ist(end_time) if end_time.tzinfo else ensure_ist(end_time)
                
            async def _create_booking_operation():
                # Validate booking data
                await self._validate_booking_request(
                    user_id, lot_id, vehicle_type, vehicle_number, start_time, end_time
                )
                
                # Find available slot
                slot = await self._find_available_slot(lot_id, vehicle_type, start_time, end_time)
                if not slot:
                    raise InsufficientSlotsError("No available slots for the requested time")
                
                # Calculate pricing
                pricing_info = await self.pricing_service.calculate_booking_price(
                    lot_id, vehicle_type, start_time, end_time
                )
                
                # Generate booking reference
                booking_reference = await self._generate_unique_booking_reference()
                
                # Create booking
                booking = await self.booking_repository.create(
                    user_id=user_id,
                    lot_id=lot_id,
                    slot_id=slot.id,
                    vehicle_type=vehicle_type.value,
                    vehicle_number=vehicle_number.upper().strip(),
                    start_time=start_time,
                    end_time=end_time,
                    total_amount=pricing_info["total_amount"],
                    booking_reference=booking_reference,
                    status=BookingStatus.PENDING.value
                )
                
                # Create slot allocation
                allocation_type = AllocationType.FULL
                allocated_space = None
                
                # Handle bike allocation in car slot
                if vehicle_type == VehicleType.BIKE and slot.slot_type == VehicleType.CAR.value:
                    allocation_type = AllocationType.PARTIAL
                    allocated_space = await self._determine_bike_space_in_car_slot(slot.id, start_time, end_time)
                
                await self.slot_allocation_repository.create_allocation(
                    booking_id=booking.id,
                    slot_id=slot.id,
                    allocation_type=allocation_type,
                    allocated_space=allocated_space
                )
                
                # Update slot status
                if allocation_type == AllocationType.FULL:
                    slot.mark_reserved()
                
                self.logger.info(
                    "Booking created successfully",
                    booking_id=booking.id,
                    user_id=user_id,
                    slot_id=slot.id,
                    vehicle_type=vehicle_type.value
                )
                
                return booking
            
            return await self.execute_in_transaction(_create_booking_operation)
            
        except (ValidationError, InsufficientSlotsError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to create booking", user_id=user_id, error=str(e))
            raise BusinessLogicError("Failed to create booking")
    
    async def cancel_booking(self, booking_id: UUID, user_id: UUID) -> bool:
        """Cancel a booking."""
        try:
            async def _cancel_booking_operation():
                # Get booking
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                # Verify user owns the booking
                if booking.user_id != user_id:
                    raise ValidationError("You can only cancel your own bookings")
                
                # Check if booking can be cancelled
                if not booking.can_cancel():
                    raise BookingNotCancellableError("Booking cannot be cancelled at this time")
                
                # Cancel booking
                booking.cancel()
                
                # Release slot allocations
                allocations = await self.slot_allocation_repository.get_by_booking(booking_id)
                for allocation in allocations:
                    if allocation.slot:
                        if allocation.allocation_type == AllocationType.FULL.value:
                            allocation.slot.mark_available()
                        # For partial allocations, check if slot can be marked available
                        elif allocation.allocation_type == AllocationType.PARTIAL.value:
                            remaining_allocations = await self._count_active_allocations_for_slot(
                                allocation.slot_id, exclude_booking_id=booking_id
                            )
                            if remaining_allocations == 0:
                                allocation.slot.mark_available()
                
                self.logger.info("Booking cancelled successfully", booking_id=booking_id, user_id=user_id)
                return True
            
            return await self.execute_in_transaction(_cancel_booking_operation)
            
        except (NotFoundError, ValidationError, BookingNotCancellableError):
            raise
        except Exception as e:
            self.logger.error("Failed to cancel booking", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to cancel booking")
    
    async def check_in_booking(self, booking_id: UUID, user_id: UUID, is_admin: bool = False) -> bool:
        """Check in to a booking."""
        try:
            async def _check_in_operation():
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                # Only check user_id if not admin
                if not is_admin and booking.user_id != user_id:
                    raise ValidationError("You can only check in to your own bookings")
                
                if not booking.can_check_in:
                    raise BusinessLogicError("Cannot check in at this time")
                
                booking.check_in()
                
                self.logger.info("Checked in to booking", booking_id=booking_id, user_id=user_id, is_admin=is_admin)
                return True
            
            return await self.execute_in_transaction(_check_in_operation)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to check in booking", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to check in")
    
    async def check_out_booking(self, booking_id: UUID, user_id: UUID) -> bool:
        """Check out from a booking."""
        try:
            async def _check_out_operation():
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                if booking.user_id != user_id:
                    raise ValidationError("You can only check out from your own bookings")
                
                if not booking.can_check_out:
                    raise BusinessLogicError("Cannot check out at this time")
                
                booking.check_out()
                
                self.logger.info("Checked out from booking", booking_id=booking_id, user_id=user_id)
                return True
            
            return await self.execute_in_transaction(_check_out_operation)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to check out booking", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to check out")
    
    async def get_booking_by_reference(self, booking_reference: str) -> Optional[Booking]:
        """Get booking by reference code."""
        try:
            booking = await self.booking_repository.get_by_reference(booking_reference)
            return booking
            
        except Exception as e:
            self.logger.error("Failed to get booking by reference", reference=booking_reference, error=str(e))
            raise BusinessLogicError("Failed to retrieve booking")
    
    async def admin_check_in_by_reference(self, booking_reference: str) -> bool:
        """Admin check-in a booking by reference code."""
        try:
            # First get the booking
            booking = await self.get_booking_by_reference(booking_reference)
            if not booking:
                raise NotFoundError("Booking not found")
            
            # Then check it in as admin
            return await self.check_in_booking(booking.id, booking.user_id, is_admin=True)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed admin check-in by reference", reference=booking_reference, error=str(e))
            raise BusinessLogicError("Failed to check in booking")
    
    async def get_user_bookings(
        self, 
        user_id: UUID, 
        status: Optional[BookingStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Booking]:
        """Get bookings for a user."""
        return await self.booking_repository.get_user_bookings(user_id, status, skip, limit)
    
    async def get_all_bookings_admin(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BookingStatus] = None,
        user_id: Optional[UUID] = None,
        lot_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Booking]:
        """Get all bookings for admin with filtering."""
        return await self.booking_repository.get_all_bookings_admin(
            skip=skip,
            limit=limit,
            status=status,
            user_id=user_id,
            lot_id=lot_id,
            start_date=start_date,
            end_date=end_date
        )
    
    async def admin_cancel_booking(self, booking_id: UUID, reason: Optional[str] = None) -> bool:
        """Admin cancel any booking."""
        try:
            async def _admin_cancel_operation():
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                if not booking.can_cancel():
                    raise BusinessLogicError("Cannot cancel this booking")
                
                booking.cancel()
                
                # Log cancellation reason if provided
                if reason:
                    self.logger.info("Admin cancelled booking", booking_id=booking_id, reason=reason)
                else:
                    self.logger.info("Admin cancelled booking", booking_id=booking_id)
                
                return True
            
            return await self.execute_in_transaction(_admin_cancel_operation)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to cancel booking", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to cancel booking")
    
    async def process_refund(self, booking_id: UUID) -> bool:
        """Process refund for a cancelled booking."""
        try:
            async def _process_refund_operation():
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                if booking.status != BookingStatus.CANCELLED.value:
                    raise BusinessLogicError("Can only refund cancelled bookings")
                
                # Here you would integrate with payment gateway for actual refund
                # For now, we'll just log the refund
                self.logger.info("Processed refund", booking_id=booking_id, amount=booking.total_amount)
                
                return True
            
            return await self.execute_in_transaction(_process_refund_operation)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to process refund", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to process refund")
    
    async def confirm_booking_after_payment(self, booking_id: UUID) -> bool:
        """Confirm booking after successful payment."""
        try:
            async def _confirm_booking_operation():
                booking = await self.booking_repository.get_by_id(booking_id, load_relationships=True)
                if not booking:
                    raise NotFoundError("Booking not found")
                
                if booking.status != BookingStatus.PENDING.value:
                    raise BusinessLogicError("Can only confirm pending bookings")
                
                # Update booking status to CONFIRMED
                booking.status = BookingStatus.CONFIRMED.value
                
                # Update user's total spent
                if booking.user:
                    booking.user.total_spent = (booking.user.total_spent or 0) + booking.total_amount
                    self.logger.info("Updated user total spent", 
                                   user_id=booking.user_id, 
                                   amount=booking.total_amount,
                                   new_total=booking.user.total_spent)
                
                self.logger.info("Booking confirmed after payment", booking_id=booking_id)
                return True
            
            return await self.execute_in_transaction(_confirm_booking_operation)
            
        except (NotFoundError, ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            self.logger.error("Failed to confirm booking after payment", booking_id=booking_id, error=str(e))
            raise BusinessLogicError("Failed to confirm booking")
    
    async def search_bookings(self, search_term: str, skip: int = 0, limit: int = 20) -> List[Booking]:
        """Search bookings."""
        return await self.booking_repository.search_bookings(search_term, skip, limit)
    
    async def get_booking_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime,
        lot_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get booking statistics."""
        return await self.booking_repository.get_booking_statistics(start_date, end_date, lot_id)
    
    async def process_expired_bookings(self) -> int:
        """Process expired bookings and mark them as expired."""
        try:
            expired_bookings = await self.booking_repository.get_expired_bookings()
            
            for booking in expired_bookings:
                async def _expire_booking():
                    booking.mark_expired()
                    
                    # Release slot allocations
                    allocations = await self.slot_allocation_repository.get_by_booking(booking.id)
                    for allocation in allocations:
                        if allocation.slot and allocation.allocation_type == AllocationType.FULL.value:
                            allocation.slot.mark_available()
                
                await self.execute_in_transaction(_expire_booking)
            
            if expired_bookings:
                self.logger.info("Processed expired bookings", count=len(expired_bookings))
            
            return len(expired_bookings)
            
        except Exception as e:
            self.logger.error("Failed to process expired bookings", error=str(e))
            return 0
    
    async def process_no_show_bookings(self, grace_period_minutes: int = 15) -> int:
        """Process no-show bookings."""
        try:
            no_show_bookings = await self.booking_repository.get_no_show_bookings(grace_period_minutes)
            
            for booking in no_show_bookings:
                async def _mark_no_show():
                    booking.mark_no_show()
                    
                    # Release slot allocations
                    allocations = await self.slot_allocation_repository.get_by_booking(booking.id)
                    for allocation in allocations:
                        if allocation.slot and allocation.allocation_type == AllocationType.FULL.value:
                            allocation.slot.mark_available()
                
                await self.execute_in_transaction(_mark_no_show)
            
            if no_show_bookings:
                self.logger.info("Processed no-show bookings", count=len(no_show_bookings))
            
            return len(no_show_bookings)
            
        except Exception as e:
            self.logger.error("Failed to process no-show bookings", error=str(e))
            return 0
    
    async def _validate_booking_request(
        self,
        user_id: UUID,
        lot_id: UUID,
        vehicle_type: VehicleType,
        vehicle_number: str,
        start_time: datetime,
        end_time: datetime
    ) -> None:
        """Validate booking request data."""
        # Validate user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        if not user.is_active:
            raise UserNotActiveError("User account is not active")
        
        # Validate parking lot
        lot = await self.parking_lot_repository.get_by_id(lot_id)
        if not lot:
            raise NotFoundError("Parking lot not found")
        if not lot.is_active:
            raise ParkingLotNotActiveError("Parking lot is not active")
        
        # Ensure all datetimes are timezone-aware for consistent comparison
        now = ist_now()
        
        # Convert naive datetimes to IST if necessary
        start_time = to_ist(start_time) if start_time.tzinfo else ensure_ist(start_time)
        end_time = to_ist(end_time) if end_time.tzinfo else ensure_ist(end_time)
        
        # Validate time range
        if start_time <= now:
            raise InvalidTimeRangeError("Booking start time must be in the future")
        if end_time <= start_time:
            raise InvalidTimeRangeError("End time must be after start time")
        
        max_duration = timedelta(hours=settings.max_booking_duration_hours)
        if end_time - start_time > max_duration:
            raise InvalidTimeRangeError(f"Maximum booking duration is {settings.max_booking_duration_hours} hours")
        
        # Validate vehicle number
        if not vehicle_number or len(vehicle_number.strip()) < 3:
            raise ValidationError("Valid vehicle number is required")
    
    async def _find_available_slot(
        self,
        lot_id: UUID,
        vehicle_type: VehicleType,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[ParkingSlot]:
        """Find an available slot for booking."""
        try:
            available_slots = await self.parking_slot_repository.get_available_slots(
                lot_id, vehicle_type, start_time, end_time, limit=1
            )
            
            if available_slots:
                return available_slots[0]
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to find available slot", lot_id=lot_id, error=str(e))
            return None
    
    async def _generate_unique_booking_reference(self) -> str:
        """Generate unique booking reference."""
        max_attempts = 10
        for _ in range(max_attempts):
            reference = Booking.generate_reference()
            existing = await self.booking_repository.get_by_reference(reference)
            if not existing:
                return reference
        
        raise BusinessLogicError("Failed to generate unique booking reference")
    
    async def _determine_bike_space_in_car_slot(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Determine which part of car slot to allocate for bike."""
        # Check existing bike allocations in this car slot
        existing_allocations = await self.slot_allocation_repository.get_by_slot(
            slot_id, start_time, end_time
        )
        
        bike_allocations = [
            alloc for alloc in existing_allocations 
            if alloc.allocation_type == AllocationType.PARTIAL.value
        ]
        
        if len(bike_allocations) == 0:
            return "left_half"
        elif len(bike_allocations) == 1:
            existing_space = bike_allocations[0].allocated_space
            return "right_half" if existing_space == "left_half" else "left_half"
        else:
            # This shouldn't happen if validation is correct
            raise BusinessLogicError("Car slot is already fully occupied by bikes")
    
    async def _count_active_allocations_for_slot(
        self,
        slot_id: UUID,
        exclude_booking_id: Optional[UUID] = None
    ) -> int:
        """Count active allocations for a slot."""
        try:
            # This would need to be implemented in the repository
            # For now, returning 0 as placeholder
            return 0
            
        except Exception as e:
            self.logger.error("Failed to count allocations", slot_id=slot_id, error=str(e))
            return 0
    
    def _get_entity_name(self) -> str:
        """Get entity name for base service."""
        return "Booking"
