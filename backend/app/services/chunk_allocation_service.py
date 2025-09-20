"""
Chunk Allocation Service

Handles the precise allocation of 1-minute chunks for booking durations,
including buffer time calculations and conflict resolution.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.slot_chunks import SlotTimeChunk, DemandLevel, GenerationStrategy, ChunkStatus
from app.models.booking import Booking, BookingStatus
from app.repositories.slot_chunks import SlotTimeChunkRepository
from app.services.hybrid_duration_calculator import duration_calculator
from app.services.smart_chunk_manager import create_smart_chunk_manager, ChunkGenerationRequest, ChunkGenerationMode
from app.core.config import get_settings
from app.core.cache import cache_manager
from app.core.locks import slot_lock_manager

logger = structlog.get_logger(__name__)


class AllocationStrategy(str, Enum):
    """Chunk allocation strategies."""
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    EXACT_FIT = "exact_fit"
    BUFFER_AWARE = "buffer_aware"


@dataclass
class ChunkAllocationRequest:
    """Request for chunk allocation."""
    slot_id: UUID
    booking_start: datetime
    booking_duration: int
    demand_level: DemandLevel = DemandLevel.MEDIUM
    allocation_strategy: AllocationStrategy = AllocationStrategy.BUFFER_AWARE
    user_id: Optional[UUID] = None
    include_buffer: bool = True


@dataclass
class ChunkAllocationResult:
    """Result of chunk allocation."""
    allocated_chunks: List[SlotTimeChunk]
    booking_end_time: datetime
    slot_release_time: datetime
    buffer_minutes: int
    total_chunks: int
    allocation_successful: bool
    conflict_details: Optional[Dict] = None
    suggested_alternatives: List[Tuple[datetime, datetime]] = None
    
    def __post_init__(self):
        if self.suggested_alternatives is None:
            self.suggested_alternatives = []


class ChunkAllocationService:
    """
    Service for allocating chunks to bookings with precision and buffer awareness.
    
    Handles:
    - Precise 1-minute chunk allocation
    - Buffer time integration
    - Conflict detection and resolution
    - Demand-aware optimization
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize chunk allocation service."""
        self.session = session
        self.chunk_repository = SlotTimeChunkRepository(session)
        self.smart_chunk_manager = create_smart_chunk_manager(session)
        from app.core.config import settings
        self.settings = settings
        self.duration_calculator = duration_calculator
        self.logger = logger.bind(service="ChunkAllocationService")
    
    async def allocate_chunks_for_booking(
        self, 
        request: ChunkAllocationRequest
    ) -> ChunkAllocationResult:
        """
        Allocate precise chunks for a booking with buffer awareness.
        
        Args:
            request: Chunk allocation request
            
        Returns:
            ChunkAllocationResult with allocation details
        """
        try:
            # Use distributed locks to prevent race conditions
            async with slot_lock_manager.lock_slot_allocation(
                slot_id=str(request.slot_id),
                user_id=str(request.user_id) if request.user_id else "system",
                operation="chunk_allocation"
            ) as allocation_lock:
                
                self.logger.info(
                    "Starting chunk allocation",
                    slot_id=request.slot_id,
                    booking_start=request.booking_start.isoformat(),
                    duration=request.booking_duration,
                    demand_level=request.demand_level.value
                )
                
                # Calculate booking and slot release times with buffer
                booking_end_time, slot_release_time, buffer_minutes = (
                    self.duration_calculator.calculate_actual_end_time(
                        request.booking_start, 
                        request.booking_duration, 
                        request.demand_level.value
                    )
                )
                
                # Check for existing chunk conflicts
                existing_chunks = await self._get_conflicting_chunks(
                    request.slot_id, 
                    request.booking_start, 
                    slot_release_time if request.include_buffer else booking_end_time
                )
                
                if existing_chunks:
                    return await self._handle_chunk_conflicts(
                        request, existing_chunks, booking_end_time, slot_release_time, buffer_minutes
                    )
                
                # Generate or find required chunks
                required_chunks = await self._get_or_create_required_chunks(
                    request, booking_end_time, slot_release_time
                )
                
                # Allocate chunks using selected strategy
                allocated_chunks = await self._allocate_chunks_by_strategy(
                    request, required_chunks, booking_end_time
                )
                
                result = ChunkAllocationResult(
                    allocated_chunks=allocated_chunks,
                    booking_end_time=booking_end_time,
                    slot_release_time=slot_release_time,
                    buffer_minutes=buffer_minutes,
                    total_chunks=len(allocated_chunks),
                    allocation_successful=True
                )
                
                self.logger.info(
                    "Chunk allocation completed successfully",
                    slot_id=request.slot_id,
                    total_chunks=result.total_chunks,
                    buffer_minutes=result.buffer_minutes
                )
                
                return result
                
        except Exception as e:
            self.logger.error(
                "Error during chunk allocation",
                slot_id=request.slot_id,
                error=str(e)
            )
            
            return ChunkAllocationResult(
                allocated_chunks=[],
                booking_end_time=request.booking_start + timedelta(minutes=request.booking_duration),
                slot_release_time=request.booking_start + timedelta(minutes=request.booking_duration),
                buffer_minutes=0,
                total_chunks=0,
                allocation_successful=False,
                conflict_details={"error": str(e)}
            )
    
    async def _get_conflicting_chunks(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Find existing chunks that conflict with the requested time range."""
        
        query = select(SlotTimeChunk).where(
            and_(
                SlotTimeChunk.slot_id == slot_id,
                SlotTimeChunk.status.in_([ChunkStatus.BOOKED.value, ChunkStatus.TEMP_RESERVED.value]),
                or_(
                    # Chunk starts during our time range
                    and_(
                        SlotTimeChunk.start_time >= start_time,
                        SlotTimeChunk.start_time < end_time
                    ),
                    # Chunk ends during our time range
                    and_(
                        SlotTimeChunk.end_time > start_time,
                        SlotTimeChunk.end_time <= end_time
                    ),
                    # Chunk completely encompasses our time range
                    and_(
                        SlotTimeChunk.start_time <= start_time,
                        SlotTimeChunk.end_time >= end_time
                    )
                )
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _handle_chunk_conflicts(
        self,
        request: ChunkAllocationRequest,
        conflicting_chunks: List[SlotTimeChunk],
        booking_end_time: datetime,
        slot_release_time: datetime,
        buffer_minutes: int
    ) -> ChunkAllocationResult:
        """Handle conflicts with existing chunks."""
        
        conflict_details = {
            "conflicting_chunks": len(conflicting_chunks),
            "conflict_times": [
                {
                    "start": chunk.start_time.isoformat(),
                    "end": chunk.end_time.isoformat(),
                    "status": chunk.status
                }
                for chunk in conflicting_chunks
            ]
        }
        
        # Generate alternative time slots
        suggested_alternatives = await self._generate_alternative_slots(
            request, conflicting_chunks
        )
        
        self.logger.warning(
            "Chunk allocation conflict detected",
            slot_id=request.slot_id,
            conflicting_chunks=len(conflicting_chunks),
            alternatives_generated=len(suggested_alternatives)
        )
        
        return ChunkAllocationResult(
            allocated_chunks=[],
            booking_end_time=booking_end_time,
            slot_release_time=slot_release_time,
            buffer_minutes=buffer_minutes,
            total_chunks=0,
            allocation_successful=False,
            conflict_details=conflict_details,
            suggested_alternatives=suggested_alternatives
        )
    
    async def _generate_alternative_slots(
        self,
        request: ChunkAllocationRequest,
        conflicting_chunks: List[SlotTimeChunk]
    ) -> List[Tuple[datetime, datetime]]:
        """Generate alternative time slots avoiding conflicts."""
        
        alternatives = []
        
        # Find gaps between conflicting chunks
        sorted_conflicts = sorted(conflicting_chunks, key=lambda c: c.start_time)
        
        # Try slot before first conflict
        if sorted_conflicts:
            first_conflict = sorted_conflicts[0]
            alt_end = first_conflict.start_time
            alt_start = alt_end - timedelta(minutes=request.booking_duration)
            
            if alt_start >= datetime.now(timezone.utc):
                alternatives.append((alt_start, alt_start + timedelta(minutes=request.booking_duration)))
        
        # Try slots between conflicts
        for i in range(len(sorted_conflicts) - 1):
            current_end = sorted_conflicts[i].end_time
            next_start = sorted_conflicts[i + 1].start_time
            
            gap_minutes = int((next_start - current_end).total_seconds() / 60)
            buffer_time = self.duration_calculator.calculate_buffer_time(
                request.booking_duration, request.demand_level.value
            )
            
            if gap_minutes >= request.booking_duration + buffer_time:
                alt_start = current_end
                alt_end = alt_start + timedelta(minutes=request.booking_duration)
                alternatives.append((alt_start, alt_end))
        
        # Try slot after last conflict
        if sorted_conflicts:
            last_conflict = sorted_conflicts[-1]
            alt_start = last_conflict.end_time
            alt_end = alt_start + timedelta(minutes=request.booking_duration)
            alternatives.append((alt_start, alt_end))
        
        return alternatives[:3]  # Return top 3 alternatives
    
    async def _get_or_create_required_chunks(
        self,
        request: ChunkAllocationRequest,
        booking_end_time: datetime,
        slot_release_time: datetime
    ) -> List[SlotTimeChunk]:
        """Get existing chunks or create new ones for the booking time range."""
        
        # Check if chunks already exist for this time range
        existing_chunks = await self._get_available_chunks_in_range(
            request.slot_id, request.booking_start, booking_end_time
        )
        
        if len(existing_chunks) > 0:
            # Use existing chunks if available
            return existing_chunks
        
        # Generate new chunks using smart chunk manager
        generated_chunks_data = await self.smart_chunk_manager.generate_chunks_for_booking_duration(
            request.slot_id,
            request.booking_start,
            request.booking_duration,
            request.demand_level
        )
        
        # Create SlotTimeChunk objects from generated data
        chunks = []
        for chunk_data in generated_chunks_data:
            chunk = SlotTimeChunk(
                slot_id=chunk_data["slot_id"],
                start_time=chunk_data["start_time"],
                end_time=chunk_data["end_time"],
                chunk_size_minutes=chunk_data["chunk_size_minutes"],
                demand_level=chunk_data["demand_level"],
                generation_strategy=chunk_data["generation_strategy"],
                status=ChunkStatus.AVAILABLE.value
            )
            chunks.append(chunk)
        
        # Save new chunks to database
        for chunk in chunks:
            self.session.add(chunk)
        await self.session.flush()
        
        return chunks
    
    async def _get_available_chunks_in_range(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Get available chunks within a specific time range."""
        
        query = select(SlotTimeChunk).where(
            and_(
                SlotTimeChunk.slot_id == slot_id,
                SlotTimeChunk.status == ChunkStatus.AVAILABLE.value,
                SlotTimeChunk.start_time >= start_time,
                SlotTimeChunk.end_time <= end_time
            )
        ).order_by(SlotTimeChunk.start_time)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _allocate_chunks_by_strategy(
        self,
        request: ChunkAllocationRequest,
        available_chunks: List[SlotTimeChunk],
        booking_end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Allocate chunks using the specified strategy."""
        
        if request.allocation_strategy == AllocationStrategy.EXACT_FIT:
            return await self._allocate_exact_fit(available_chunks, request.booking_duration)
        elif request.allocation_strategy == AllocationStrategy.BEST_FIT:
            return await self._allocate_best_fit(available_chunks, request.booking_duration)
        elif request.allocation_strategy == AllocationStrategy.BUFFER_AWARE:
            return await self._allocate_buffer_aware(available_chunks, request, booking_end_time)
        else:  # FIRST_FIT
            return await self._allocate_first_fit(available_chunks, request.booking_duration)
    
    async def _allocate_exact_fit(
        self, 
        available_chunks: List[SlotTimeChunk], 
        duration_minutes: int
    ) -> List[SlotTimeChunk]:
        """Allocate chunks that exactly match the duration."""
        allocated = []
        total_allocated = 0
        
        for chunk in available_chunks:
            if total_allocated >= duration_minutes:
                break
            
            if total_allocated + chunk.chunk_size_minutes <= duration_minutes:
                allocated.append(chunk)
                total_allocated += chunk.chunk_size_minutes
        
        return allocated if total_allocated == duration_minutes else []
    
    async def _allocate_best_fit(
        self, 
        available_chunks: List[SlotTimeChunk], 
        duration_minutes: int
    ) -> List[SlotTimeChunk]:
        """Allocate chunks with minimum waste."""
        # Sort chunks by size (smallest first for best fit)
        sorted_chunks = sorted(available_chunks, key=lambda c: c.chunk_size_minutes)
        
        allocated = []
        total_allocated = 0
        
        for chunk in sorted_chunks:
            if total_allocated >= duration_minutes:
                break
            
            if total_allocated + chunk.chunk_size_minutes <= duration_minutes:
                allocated.append(chunk)
                total_allocated += chunk.chunk_size_minutes
        
        return allocated
    
    async def _allocate_first_fit(
        self, 
        available_chunks: List[SlotTimeChunk], 
        duration_minutes: int
    ) -> List[SlotTimeChunk]:
        """Allocate chunks in order until duration is met."""
        allocated = []
        total_allocated = 0
        
        for chunk in available_chunks:
            if total_allocated >= duration_minutes:
                break
            
            allocated.append(chunk)
            total_allocated += chunk.chunk_size_minutes
        
        return allocated
    
    async def _allocate_buffer_aware(
        self, 
        available_chunks: List[SlotTimeChunk], 
        request: ChunkAllocationRequest,
        booking_end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Allocate chunks considering buffer time requirements."""
        allocated = []
        current_time = request.booking_start
        
        for chunk in available_chunks:
            if current_time >= booking_end_time:
                break
            
            # Check if chunk is contiguous with our allocation
            if chunk.start_time <= current_time and chunk.end_time > current_time:
                allocated.append(chunk)
                current_time = chunk.end_time
            elif chunk.start_time == current_time:
                allocated.append(chunk)
                current_time = chunk.end_time
        
        return allocated
    
    async def mark_chunks_as_reserved(
        self, 
        chunks: List[SlotTimeChunk], 
        user_id: UUID,
        booking_id: Optional[UUID] = None
    ) -> bool:
        """Mark chunks as temporarily reserved or booked."""
        try:
            for chunk in chunks:
                if booking_id:
                    chunk.mark_booked(booking_id)
                else:
                    chunk.mark_temp_reserved(user_id)
            
            await self.session.flush()
            return True
            
        except Exception as e:
            self.logger.error(
                "Error marking chunks as reserved",
                chunk_count=len(chunks),
                user_id=user_id,
                error=str(e)
            )
            return False
    
    async def release_chunks(self, chunks: List[SlotTimeChunk]) -> bool:
        """Release chunks back to available status."""
        try:
            for chunk in chunks:
                chunk.mark_available()
            
            await self.session.flush()
            return True
            
        except Exception as e:
            self.logger.error(
                "Error releasing chunks",
                chunk_count=len(chunks),
                error=str(e)
            )
            return False
    
    async def get_chunk_utilization_stats(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict:
        """Get utilization statistics for chunks in a time range."""
        
        query = select(SlotTimeChunk).where(
            and_(
                SlotTimeChunk.slot_id == slot_id,
                SlotTimeChunk.start_time >= start_time,
                SlotTimeChunk.end_time <= end_time
            )
        )
        
        result = await self.session.execute(query)
        chunks = result.scalars().all()
        
        if not chunks:
            return {
                "total_chunks": 0,
                "utilization_rate": 0.0,
                "status_breakdown": {}
            }
        
        status_counts = {}
        for chunk in chunks:
            status = chunk.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_chunks = len(chunks)
        booked_chunks = status_counts.get(ChunkStatus.BOOKED.value, 0)
        reserved_chunks = status_counts.get(ChunkStatus.TEMP_RESERVED.value, 0)
        
        utilization_rate = (booked_chunks + reserved_chunks) / total_chunks if total_chunks > 0 else 0
        
        return {
            "total_chunks": total_chunks,
            "utilization_rate": round(utilization_rate, 3),
            "status_breakdown": status_counts,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }


# Factory function for dependency injection
def create_chunk_allocation_service(session: AsyncSession) -> ChunkAllocationService:
    """Factory function to create ChunkAllocationService instance."""
    return ChunkAllocationService(session)
