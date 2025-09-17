"""Repository for SlotTimeChunk model operations."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.repositories.base import BaseRepository
from app.models.slot_chunks import SlotTimeChunk, ChunkStatus
from app.core.config import settings
from app.core.timezone import now as ist_now


logger = structlog.get_logger(__name__)


class SlotTimeChunkRepository(BaseRepository[SlotTimeChunk]):
    """Repository for SlotTimeChunk model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotTimeChunk)
    
    async def generate_chunks_for_slot(
        self,
        slot_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[SlotTimeChunk]:
        """Generate 30-minute chunks for a slot within date range."""
        try:
            chunks_to_create = []
            
            # Start from the beginning of the hour (either :00 or :30)
            current = start_date.replace(second=0, microsecond=0)
            if current.minute < 30:
                current = current.replace(minute=0)
            else:
                current = current.replace(minute=30)
            
            while current < end_date:
                chunk_start = current
                chunk_end = current + timedelta(minutes=settings.slot_time_chunk_size)
                
                # Only create chunks with future end times
                if chunk_end > ist_now():
                    # Check if chunk already exists
                    existing = await self.session.execute(
                        select(SlotTimeChunk).where(
                            and_(
                                SlotTimeChunk.slot_id == slot_id,
                                SlotTimeChunk.start_time == chunk_start,
                                SlotTimeChunk.end_time == chunk_end
                            )
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        chunk = SlotTimeChunk(
                            slot_id=slot_id,
                            start_time=chunk_start,
                            end_time=chunk_end,
                            status=ChunkStatus.AVAILABLE.value
                        )
                        chunks_to_create.append(chunk)
                
                current = chunk_end
            
            # Bulk insert new chunks
            if chunks_to_create:
                self.session.add_all(chunks_to_create)
                await self.session.flush()
                
                logger.info(
                    "Generated chunks for slot",
                    slot_id=slot_id,
                    chunks_created=len(chunks_to_create),
                    time_range=f"{start_date} to {end_date}"
                )
            
            return chunks_to_create
            
        except Exception as e:
            logger.error("Failed to generate chunks", slot_id=slot_id, error=str(e))
            raise
    
    async def get_slot_availability_by_chunks(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get chunk-based availability for a slot."""
        try:
            # Get all chunks in the time range
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time,
                    SlotTimeChunk.end_time > ist_now()  # Only future chunks
                )
            ).order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            chunks = list(result.scalars().all())
            
            # Calculate availability statistics
            total_chunks = len(chunks)
            available_chunks = sum(1 for chunk in chunks if chunk.status == ChunkStatus.AVAILABLE.value)
            booked_chunks = sum(1 for chunk in chunks if chunk.status == ChunkStatus.BOOKED.value)
            temp_reserved_chunks = sum(1 for chunk in chunks if chunk.status == ChunkStatus.TEMP_RESERVED.value)
            
            availability_rate = (available_chunks / total_chunks * 100) if total_chunks > 0 else 0
            
            # Convert chunks to dict format and check Redis locks
            chunk_data = []
            for chunk in chunks:
                chunk_status = chunk.status
                
                # Check Redis for temporary reservations
                from app.core.cache import ChunkReservationCache
                if chunk_status == "available" and await ChunkReservationCache.is_chunk_reserved(str(chunk.id)):
                    chunk_status = "temp_reserved"
                
                chunk_data.append({
                    "id": str(chunk.id),
                    "start_time": chunk.start_time.isoformat(),
                    "end_time": chunk.end_time.isoformat(),
                    "status": chunk_status,
                    "booking_id": str(chunk.booking_id) if chunk.booking_id else None,
                    "reserved_by": str(chunk.reserved_by) if chunk.reserved_by else None
                })
            
            # Recalculate counts with Redis status
            available_chunks = sum(1 for chunk in chunk_data if chunk["status"] == "available")
            booked_chunks = sum(1 for chunk in chunk_data if chunk["status"] == "booked")
            temp_reserved_chunks = sum(1 for chunk in chunk_data if chunk["status"] == "temp_reserved")
            
            return {
                "total_chunks": total_chunks,
                "available_chunks": available_chunks,
                "booked_chunks": booked_chunks,
                "temp_reserved_chunks": temp_reserved_chunks,
                "availability_rate": round(availability_rate, 2),
                "chunks": chunk_data
            }
            
        except Exception as e:
            logger.error("Failed to get slot availability", slot_id=slot_id, error=str(e))
            raise
    
    async def get_available_chunks(
        self,
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[SlotTimeChunk]:
        """Get available chunks for booking."""
        try:
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time,
                    SlotTimeChunk.status == ChunkStatus.AVAILABLE.value,
                    SlotTimeChunk.end_time > ist_now()
                )
            ).order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get available chunks", slot_id=slot_id, error=str(e))
            raise
    
    async def reserve_chunks_temp(
        self,
        chunk_ids: List[UUID],
        user_id: UUID
    ) -> bool:
        """Temporarily reserve chunks (database level)."""
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
                    reserved_at=ist_now()
                )
            )
            
            result = await self.session.execute(query)
            updated_count = result.rowcount
            
            if updated_count != len(chunk_ids):
                # Some chunks were not available, rollback
                await self.session.rollback()
                return False
            
            await self.session.commit()
            
            logger.info(
                "Chunks temporarily reserved",
                chunk_count=updated_count,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to reserve chunks", chunk_ids=chunk_ids, error=str(e))
            await self.session.rollback()
            raise
    
    async def confirm_chunks_booking(
        self,
        chunk_ids: List[UUID],
        booking_id: UUID
    ) -> bool:
        """Confirm chunk booking (convert temp_reserved to booked)."""
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
            
            logger.info(
                "Chunks confirmed for booking",
                chunk_count=updated_count,
                booking_id=booking_id
            )
            
            return updated_count == len(chunk_ids)
            
        except Exception as e:
            logger.error("Failed to confirm chunks", chunk_ids=chunk_ids, error=str(e))
            raise
    
    async def release_chunks(
        self,
        chunk_ids: List[UUID],
        user_id: Optional[UUID] = None
    ) -> bool:
        """Release temporarily reserved chunks."""
        try:
            conditions = [
                SlotTimeChunk.id.in_(chunk_ids),
                SlotTimeChunk.status == ChunkStatus.TEMP_RESERVED.value
            ]
            
            if user_id:
                conditions.append(SlotTimeChunk.reserved_by == user_id)
            
            query = (
                update(SlotTimeChunk)
                .where(and_(*conditions))
                .values(
                    status=ChunkStatus.AVAILABLE.value,
                    reserved_by=None,
                    reserved_at=None
                )
            )
            
            result = await self.session.execute(query)
            released_count = result.rowcount
            
            logger.info(
                "Chunks released",
                chunk_count=released_count,
                user_id=user_id
            )
            
            return released_count > 0
            
        except Exception as e:
            logger.error("Failed to release chunks", chunk_ids=chunk_ids, error=str(e))
            raise
    
    async def cleanup_expired_reservations(self, expiry_minutes: int = 10) -> int:
        """Clean up expired temporary reservations."""
        try:
            expiry_time = ist_now() - timedelta(minutes=expiry_minutes)
            
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
                logger.info("Cleaned up expired reservations", count=cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired reservations", error=str(e))
            raise
