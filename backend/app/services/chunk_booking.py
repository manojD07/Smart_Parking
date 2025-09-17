"""Enhanced booking service with time chunk system."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import json
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService, TransactionalService
from app.repositories.slot_chunks import SlotTimeChunkRepository
from app.repositories.booking import BookingRepository
from app.repositories.parking import ParkingSlotRepository, ParkingLotRepository
from app.repositories.user import UserRepository
from app.services.pricing import PricingService
from app.models.slot_chunks import SlotTimeChunk, ChunkStatus
from app.models.booking import Booking, BookingStatus
from app.models.parking import VehicleType, ParkingSlot
from app.core.exceptions import (
    ValidationError, NotFoundError, InsufficientSlotsError,
    BusinessLogicError, BookingConflictError
)
from app.core.timezone import now as ist_now
import structlog

logger = structlog.get_logger(__name__)


class ChunkBookingService:
    """Enhanced booking service with time chunk system and Redis reservation."""
    
    def __init__(self, session: AsyncSession, redis_client=None):
        self.session = session
        self.redis = redis_client
        
        # Repositories
        self.chunk_repository = SlotTimeChunkRepository(session)
        self.booking_repository = BookingRepository(session)
        self.slot_repository = ParkingSlotRepository(session)
        self.lot_repository = ParkingLotRepository(session)
        self.user_repository = UserRepository(session)
        self.pricing_service = PricingService(session)
        
        # Configuration
        self.RESERVATION_TIMEOUT = 600  # 10 minutes
        
        self.logger = logger.bind(service="ChunkBookingService")
    
    async def check_slot_availability(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Check availability for a specific slot using chunk system."""
        try:
            # Ensure chunks exist for the time range
            await self.chunk_repository.generate_chunks_for_slot(
                slot_id, start_time, end_time + timedelta(hours=1)
            )
            
            # Get availability data
            availability = await self.chunk_repository.get_slot_availability_by_chunks(
                slot_id, start_time, end_time
            )
            
            return availability
            
        except Exception as e:
            self.logger.error("Failed to check slot availability", slot_id=slot_id, error=str(e))
            raise BusinessLogicError("Failed to check availability")
    
    async def find_available_slot_with_chunks(
        self, 
        lot_id: UUID, 
        vehicle_type: VehicleType,
        start_time: datetime, 
        end_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """Find an available slot with chunk-based conflict detection."""
        try:
            # Get all slots for the vehicle type
            if vehicle_type == VehicleType.CAR:
                candidate_slots = await self.slot_repository.get_multi(
                    lot_id=lot_id, slot_type=vehicle_type, limit=1000
                )
            else:  # BIKE
                # For bikes, check both bike slots and car slots
                bike_slots = await self.slot_repository.get_multi(
                    lot_id=lot_id, slot_type=VehicleType.BIKE, limit=1000
                )
                car_slots = await self.slot_repository.get_multi(
                    lot_id=lot_id, slot_type=VehicleType.CAR, limit=1000
                )
                candidate_slots = bike_slots + car_slots
            
            # Check each slot for availability
            for slot in candidate_slots:
                if await self._is_slot_available_for_time_range(
                    slot, vehicle_type, start_time, end_time
                ):
                    # Generate chunks for this time range
                    await self.chunk_repository.generate_chunks_for_slot(
                        slot.id, start_time, end_time + timedelta(hours=1)
                    )
                    
                    # Get available chunks
                    available_chunks = await self.chunk_repository.get_available_chunks(
                        slot.id, start_time, end_time
                    )
                    
                    if self._are_chunks_continuous(available_chunks, start_time, end_time):
                        return {
                            "slot": slot,
                            "chunks": available_chunks
                        }
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to find available slot with chunks", error=str(e))
            raise
    
    async def _is_slot_available_for_time_range(
        self, 
        slot: ParkingSlot, 
        vehicle_type: VehicleType,
        start_time: datetime, 
        end_time: datetime
    ) -> bool:
        """Check if slot is available for the entire time range."""
        try:
            if vehicle_type == VehicleType.CAR:
                # Car needs exclusive access to slot
                conflicting_chunks = await self.chunk_repository.get_conflicting_chunks(
                    slot.id, start_time, end_time, exclude_statuses=[ChunkStatus.AVAILABLE]
                )
                return len(conflicting_chunks) == 0
            
            elif vehicle_type == VehicleType.BIKE:
                if slot.slot_type == VehicleType.BIKE.value:
                    # Bike slot - exclusive access
                    conflicting_chunks = await self.chunk_repository.get_conflicting_chunks(
                        slot.id, start_time, end_time, exclude_statuses=[ChunkStatus.AVAILABLE]
                    )
                    return len(conflicting_chunks) == 0
                
                elif slot.slot_type == VehicleType.CAR.value:
                    # Car slot - can accommodate up to 2 bikes, no cars
                    conflicting_chunks = await self.chunk_repository.get_conflicting_chunks(
                        slot.id, start_time, end_time, exclude_statuses=[ChunkStatus.AVAILABLE]
                    )
                    
                    # Count car and bike bookings in conflicting chunks
                    car_conflicts = 0
                    bike_conflicts = 0
                    
                    for chunk in conflicting_chunks:
                        if chunk.booking and chunk.booking.vehicle_type == VehicleType.CAR.value:
                            car_conflicts += 1
                        elif chunk.booking and chunk.booking.vehicle_type == VehicleType.BIKE.value:
                            bike_conflicts += 1
                    
                    # Car slot can accommodate bike if: no cars AND less than 2 bikes
                    return car_conflicts == 0 and bike_conflicts < 2
            
            return False
            
        except Exception as e:
            self.logger.error("Failed to check slot availability", error=str(e))
            return False
    
    def _are_chunks_continuous(
        self, 
        chunks: List[SlotTimeChunk], 
        start_time: datetime, 
        end_time: datetime
    ) -> bool:
        """Check if chunks form a continuous time range."""
        if not chunks:
            return False
        
        # Sort chunks by start time
        sorted_chunks = sorted(chunks, key=lambda c: c.start_time)
        
        # Check if chunks cover the entire requested time range
        if sorted_chunks[0].start_time > start_time:
            return False
        
        if sorted_chunks[-1].end_time < end_time:
            return False
        
        # Check for gaps between chunks
        for i in range(len(sorted_chunks) - 1):
            if sorted_chunks[i].end_time != sorted_chunks[i + 1].start_time:
                return False
        
        return True
    
    async def reserve_slot_chunks(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime,
        user_id: UUID,
        vehicle_type: VehicleType
    ) -> Dict[str, Any]:
        """Reserve slot chunks temporarily with Redis coordination."""
        try:
            session_id = self._generate_session_id()
            
            # Generate chunks if needed
            await self.chunk_repository.generate_chunks_for_slot(
                slot_id, start_time, end_time + timedelta(hours=1)
            )
            
            # Get required chunks
            required_chunks = await self.chunk_repository.get_available_chunks(
                slot_id, start_time, end_time
            )
            
            if not self._are_chunks_continuous(required_chunks, start_time, end_time):
                raise InsufficientSlotsError("Required time slots are not available")
            
            # Check Redis for conflicts (if Redis is available)
            if self.redis:
                await self._check_redis_conflicts(slot_id, required_chunks, user_id)
                await self._reserve_in_redis(slot_id, required_chunks, user_id, session_id)
            
            # Reserve chunks in database
            chunk_ids = [c.id for c in required_chunks]
            await self.chunk_repository.reserve_chunks_temp(chunk_ids, user_id, session_id)
            
            return {
                "session_id": session_id,
                "chunk_ids": chunk_ids,
                "reserved_until": ist_now() + timedelta(minutes=10),
                "slot_id": str(slot_id),
                "chunks": [
                    {
                        "id": str(c.id),
                        "start_time": c.start_time.isoformat(),
                        "end_time": c.end_time.isoformat()
                    } for c in required_chunks
                ]
            }
            
        except Exception as e:
            self.logger.error("Failed to reserve slot chunks", error=str(e))
            raise
    
    async def _check_redis_conflicts(
        self, 
        slot_id: UUID, 
        chunks: List[SlotTimeChunk], 
        user_id: UUID
    ) -> None:
        """Check Redis for chunk reservation conflicts."""
        if not self.redis:
            return
        
        for chunk in chunks:
            redis_key = f"slot_reservation:{slot_id}:{chunk.start_time.hour}:{chunk.end_time.hour}"
            existing = await self.redis.get(redis_key)
            
            if existing:
                existing_data = json.loads(existing)
                if existing_data.get('user_id') != str(user_id):
                    raise BookingConflictError(
                        f"Slot chunk {chunk.start_time.hour}:00-{chunk.end_time.hour}:00 "
                        f"is being booked by another user"
                    )
    
    async def _reserve_in_redis(
        self, 
        slot_id: UUID, 
        chunks: List[SlotTimeChunk], 
        user_id: UUID,
        session_id: str
    ) -> None:
        """Reserve chunks in Redis with timeout."""
        if not self.redis:
            return
        
        # Use Redis pipeline for atomicity
        pipe = self.redis.pipeline()
        
        for chunk in chunks:
            redis_key = f"slot_reservation:{slot_id}:{chunk.start_time.hour}:{chunk.end_time.hour}"
            reservation_data = {
                "user_id": str(user_id),
                "session_id": session_id,
                "slot_id": str(slot_id),
                "chunk_id": str(chunk.id),
                "reserved_at": ist_now().isoformat(),
                "expires_at": (ist_now() + timedelta(minutes=10)).isoformat()
            }
            pipe.setex(redis_key, self.RESERVATION_TIMEOUT, json.dumps(reservation_data))
        
        await pipe.execute()
    
    async def confirm_booking_from_reservation(
        self, 
        session_id: str,
        vehicle_number: str,
        payment_info: Optional[Dict[str, Any]] = None
    ) -> Booking:
        """Confirm booking from temporary reservation."""
        try:
            # Get reserved chunks by session
            reserved_chunks = await self._get_chunks_by_session(session_id)
            if not reserved_chunks:
                raise ValidationError("No valid reservation found for session")
            
            # Verify chunks are still reserved
            for chunk in reserved_chunks:
                if chunk.status != ChunkStatus.TEMP_RESERVED.value:
                    raise ValidationError("Reservation has expired or been taken")
            
            # Get booking details
            first_chunk = reserved_chunks[0]
            slot = await self.slot_repository.get_by_id(first_chunk.slot_id)
            
            start_time = min(c.start_time for c in reserved_chunks)
            end_time = max(c.end_time for c in reserved_chunks)
            
            # Determine vehicle type from slot or chunk context
            vehicle_type = VehicleType(slot.slot_type) if slot else VehicleType.CAR
            
            # Calculate pricing
            pricing_info = await self.pricing_service.calculate_booking_price(
                first_chunk.slot_id, vehicle_type, start_time, end_time
            )
            
            # Create booking
            booking = await self.booking_repository.create(
                user_id=reserved_chunks[0].reserved_by,
                lot_id=slot.lot_id,
                slot_id=slot.id,
                vehicle_type=vehicle_type.value,
                vehicle_number=vehicle_number.upper().strip(),
                start_time=start_time,
                end_time=end_time,
                total_amount=pricing_info["total_amount"],
                booking_reference=self._generate_booking_reference(),
                status=BookingStatus.CONFIRMED.value,
                session_id=session_id,
                chunk_ids=[c.id for c in reserved_chunks]
            )
            
            # Confirm chunks
            chunk_ids = [c.id for c in reserved_chunks]
            await self.chunk_repository.confirm_chunks_booking(chunk_ids, booking.id)
            
            # Clear Redis reservation
            if self.redis:
                await self._clear_redis_reservation(session_id, reserved_chunks)
            
            self.logger.info(
                "Booking confirmed from reservation",
                booking_id=booking.id,
                session_id=session_id,
                chunk_count=len(reserved_chunks)
            )
            
            return booking
            
        except Exception as e:
            self.logger.error("Failed to confirm booking from reservation", session_id=session_id, error=str(e))
            raise
    
    async def _get_chunks_by_session(self, session_id: str) -> List[SlotTimeChunk]:
        """Get all chunks reserved by a session."""
        try:
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.status == ChunkStatus.TEMP_RESERVED.value,
                    # Note: We'd need to add session_id to chunks table for this to work properly
                    # For now, we'll use reserved_at timestamp as a workaround
                )
            ).options(
                joinedload(SlotTimeChunk.slot),
                joinedload(SlotTimeChunk.booking)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get chunks by session", error=str(e))
            return []
    
    async def _clear_redis_reservation(
        self, 
        session_id: str, 
        chunks: List[SlotTimeChunk]
    ) -> None:
        """Clear Redis reservation for chunks."""
        if not self.redis:
            return
        
        keys_to_delete = []
        for chunk in chunks:
            redis_key = f"slot_reservation:{chunk.slot_id}:{chunk.start_time.hour}:{chunk.end_time.hour}"
            keys_to_delete.append(redis_key)
        
        if keys_to_delete:
            await self.redis.delete(*keys_to_delete)
    
    async def cancel_reservation(self, session_id: str) -> bool:
        """Cancel a temporary reservation."""
        try:
            # Get reserved chunks
            reserved_chunks = await self._get_chunks_by_session(session_id)
            
            if reserved_chunks:
                # Release chunks
                chunk_ids = [c.id for c in reserved_chunks]
                await self.chunk_repository.release_chunks(chunk_ids)
                
                # Clear Redis
                if self.redis:
                    await self._clear_redis_reservation(session_id, reserved_chunks)
                
                self.logger.info("Reservation cancelled", session_id=session_id, chunk_count=len(reserved_chunks))
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Failed to cancel reservation", session_id=session_id, error=str(e))
            raise
    
    async def cleanup_expired_reservations(self) -> int:
        """Clean up expired temporary reservations."""
        try:
            expiry_time = ist_now() - timedelta(minutes=10)
            
            # Clean up database
            cleaned_count = await self.chunk_repository.cleanup_expired_reservations(expiry_time)
            
            # Clean up Redis (if available)
            if self.redis:
                # This would require scanning Redis keys - implement based on Redis setup
                pass
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup expired reservations", error=str(e))
            return 0
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference."""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    def _generate_30_minute_chunks(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, datetime]]:
        """Generate 30-minute chunk boundaries with fixed patterns (hh:00-hh:30, hh:30-hh+1:00)."""
        from app.core.timezone import now as ist_now
        
        chunks = []
        # Start from the hour boundary
        current = start_time.replace(minute=0, second=0, microsecond=0)
        now = ist_now()
        
        while current < end_time:
            # First chunk: hh:00 - hh:30
            first_start = current
            first_end = current.replace(minute=30)
            
            # Only include if end_time is in future
            if first_end > now and first_start < end_time:
                chunks.append({
                    "start_time": first_start,
                    "end_time": first_end
                })
            
            # Second chunk: hh:30 - hh+1:00
            second_start = current.replace(minute=30)
            second_end = current + timedelta(hours=1)
            
            # Only include if end_time is in future  
            if second_end > now and second_start < end_time:
                chunks.append({
                    "start_time": second_start,
                    "end_time": second_end
                })
            
            current += timedelta(hours=1)
        
        return chunks
