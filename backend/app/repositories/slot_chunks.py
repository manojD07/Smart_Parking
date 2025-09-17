"""Repository for slot time chunk operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.repositories.base import BaseRepository
from app.models.slot_chunks import SlotTimeChunk, ChunkStatus
from app.models.booking import BookingStatus
from app.core.exceptions import ValidationError, NotFoundError
import structlog

logger = structlog.get_logger(__name__)


class SlotTimeChunkRepository(BaseRepository[SlotTimeChunk]):
    """Repository for SlotTimeChunk model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotTimeChunk)
        self.logger = logger.bind(repository="SlotTimeChunkRepository")
    
    async def generate_chunks_for_slot(
        self, 
        slot_id: UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[SlotTimeChunk]:
        """Generate 30-minute chunks for a slot with fixed boundaries (hh:00-hh:30, hh:30-hh+1:00)."""
        try:
            from app.core.config import settings
            from app.core.timezone import now as ist_now
            
            chunks = []
            # Start from the hour boundary of start_date
            current_time = start_date.replace(minute=0, second=0, microsecond=0)
            now = ist_now()
            
            while current_time < end_date:
                # First chunk: hh:00 - hh:30
                first_chunk_start = current_time
                first_chunk_end = current_time.replace(minute=30)
                
                # Only create chunk if end_time is in the future
                if first_chunk_end > now:
                    existing = await self.get_chunk_by_time(slot_id, first_chunk_start, first_chunk_end)
                    if not existing:
                        chunk = SlotTimeChunk(
                            slot_id=slot_id,
                            start_time=first_chunk_start,
                            end_time=first_chunk_end,
                            status=ChunkStatus.AVAILABLE.value
                        )
                        chunks.append(chunk)
                
                # Second chunk: hh:30 - hh+1:00
                second_chunk_start = current_time.replace(minute=30)
                second_chunk_end = current_time + timedelta(hours=1)
                
                # Only create chunk if end_time is in the future
                if second_chunk_end > now:
                    existing = await self.get_chunk_by_time(slot_id, second_chunk_start, second_chunk_end)
                    if not existing:
                        chunk = SlotTimeChunk(
                            slot_id=slot_id,
                            start_time=second_chunk_start,
                            end_time=second_chunk_end,
                            status=ChunkStatus.AVAILABLE.value
                        )
                        chunks.append(chunk)
                
                current_time += timedelta(hours=1)
            
            if chunks:
                # Bulk create chunks
                self.session.add_all(chunks)
                await self.session.flush()
                self.logger.info(f"Generated {len(chunks)} 30-minute chunks for slot", slot_id=slot_id)
            
            return chunks
            
        except Exception as e:
            self.logger.error("Failed to generate chunks for slot", slot_id=slot_id, error=str(e))
            raise
    
    async def get_chunk_by_time(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> Optional[SlotTimeChunk]:
        """Get chunk by exact time range."""
        try:
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time == start_time,
                    SlotTimeChunk.end_time == end_time
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get chunk by time", error=str(e))
            raise
    
    async def get_available_chunks(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Get available chunks for a time range."""
        try:
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.status == ChunkStatus.AVAILABLE.value,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time
                )
            ).order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get available chunks", error=str(e))
            raise
    
    async def get_conflicting_chunks(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime,
        exclude_statuses: Optional[List[ChunkStatus]] = None
    ) -> List[SlotTimeChunk]:
        """Get chunks that conflict with given time range."""
        try:
            exclude_statuses = exclude_statuses or []
            
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    # Time overlap: (start1 < end2) AND (end1 > start2)
                    SlotTimeChunk.start_time < end_time,
                    SlotTimeChunk.end_time > start_time
                )
            )
            
            if exclude_statuses:
                query = query.where(
                    SlotTimeChunk.status.not_in([s.value for s in exclude_statuses])
                )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get conflicting chunks", error=str(e))
            raise
    
    async def reserve_chunks_temp(
        self, 
        chunk_ids: List[UUID], 
        user_id: UUID,
        session_id: str
    ) -> bool:
        """Temporarily reserve chunks for a user session."""
        try:
            # Update chunks to temp_reserved status
            query = (
                update(SlotTimeChunk)
                .where(
                    and_(
                        SlotTimeChunk.id.in_(chunk_ids),
                        SlotTimeChunk.status == ChunkStatus.AVAILABLE.value
                    )
                )
                .values(
                    status=ChunkStatus.TEMP_RESERVED.value,
                    reserved_by=user_id,
                    reserved_at=datetime.now()
                )
            )
            
            result = await self.session.execute(query)
            updated_count = result.rowcount
            
            if updated_count != len(chunk_ids):
                # Some chunks were not available
                raise ValidationError("Some chunks are no longer available")
            
            await self.session.flush()
            return True
            
        except Exception as e:
            self.logger.error("Failed to reserve chunks temporarily", error=str(e))
            raise
    
    async def confirm_chunks_booking(
        self, 
        chunk_ids: List[UUID], 
        booking_id: UUID
    ) -> bool:
        """Confirm chunks booking after payment."""
        try:
            query = (
                update(SlotTimeChunk)
                .where(
                    and_(
                        SlotTimeChunk.id.in_(chunk_ids),
                        SlotTimeChunk.status == ChunkStatus.TEMP_RESERVED.value
                    )
                )
                .values(
                    status=ChunkStatus.BOOKED.value,
                    booking_id=booking_id,
                    reserved_by=None,
                    reserved_at=None
                )
            )
            
            result = await self.session.execute(query)
            updated_count = result.rowcount
            
            if updated_count != len(chunk_ids):
                raise ValidationError("Failed to confirm all chunks")
            
            await self.session.flush()
            return True
            
        except Exception as e:
            self.logger.error("Failed to confirm chunks booking", error=str(e))
            raise
    
    async def release_chunks(self, chunk_ids: List[UUID]) -> bool:
        """Release chunks back to available status."""
        try:
            query = (
                update(SlotTimeChunk)
                .where(SlotTimeChunk.id.in_(chunk_ids))
                .values(
                    status=ChunkStatus.AVAILABLE.value,
                    booking_id=None,
                    reserved_by=None,
                    reserved_at=None
                )
            )
            
            result = await self.session.execute(query)
            await self.session.flush()
            
            self.logger.info("Released chunks", count=result.rowcount)
            return True
            
        except Exception as e:
            self.logger.error("Failed to release chunks", error=str(e))
            raise
    
    async def cleanup_expired_reservations(self, expiry_time: datetime) -> int:
        """Clean up expired temporary reservations."""
        try:
            query = (
                update(SlotTimeChunk)
                .where(
                    and_(
                        SlotTimeChunk.status == ChunkStatus.TEMP_RESERVED.value,
                        SlotTimeChunk.reserved_at < expiry_time
                    )
                )
                .values(
                    status=ChunkStatus.AVAILABLE.value,
                    reserved_by=None,
                    reserved_at=None
                )
            )
            
            result = await self.session.execute(query)
            cleaned_count = result.rowcount
            
            if cleaned_count > 0:
                await self.session.flush()
                self.logger.info("Cleaned up expired reservations", count=cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup expired reservations", error=str(e))
            raise
    
    async def get_slot_availability_by_chunks(
        self, 
        slot_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get slot availability based on chunk system."""
        try:
            # Generate chunks if they don't exist
            await self.generate_chunks_for_slot(slot_id, start_time, end_time)
            
            # Get all chunks in time range
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time
                )
            ).order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            chunks = list(result.scalars().all())
            
            # Calculate availability stats
            total_chunks = len(chunks)
            available_chunks = len([c for c in chunks if c.status == ChunkStatus.AVAILABLE.value])
            booked_chunks = len([c for c in chunks if c.status == ChunkStatus.BOOKED.value])
            temp_reserved_chunks = len([c for c in chunks if c.status == ChunkStatus.TEMP_RESERVED.value])
            
            return {
                "total_chunks": total_chunks,
                "available_chunks": available_chunks,
                "booked_chunks": booked_chunks,
                "temp_reserved_chunks": temp_reserved_chunks,
                "availability_rate": (available_chunks / total_chunks * 100) if total_chunks > 0 else 0,
                "chunks": [
                    {
                        "id": str(c.id),
                        "start_time": c.start_time.isoformat(),
                        "end_time": c.end_time.isoformat(),
                        "status": c.status
                    } for c in chunks
                ]
            }
            
        except Exception as e:
            self.logger.error("Failed to get slot availability by chunks", error=str(e))
            raise
