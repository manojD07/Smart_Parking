"""Repository for SlotTimeChunk model operations."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.repositories.base import BaseRepository
from app.models.slot_chunks import SlotTimeChunk, ChunkStatus, DemandLevel, GenerationStrategy
from app.core.config import settings


logger = structlog.get_logger(__name__)


class SlotTimeChunkRepository(BaseRepository[SlotTimeChunk]):
    """Repository for SlotTimeChunk model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SlotTimeChunk)
    
    async def get_chunks_by_ids(self, chunk_ids: List[str]) -> List[SlotTimeChunk]:
        """Get chunks by their IDs."""
        try:
            if not chunk_ids:
                return []
            
            # Convert string IDs to UUIDs
            uuid_ids = [UUID(chunk_id) for chunk_id in chunk_ids]
            
            query = (
                select(SlotTimeChunk)
                .where(SlotTimeChunk.id.in_(uuid_ids))
                .order_by(SlotTimeChunk.start_time)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get chunks by IDs", chunk_ids=chunk_ids, error=str(e))
            return []
    
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
                if chunk_end > datetime.now(timezone.utc):
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
                    SlotTimeChunk.end_time > datetime.now(timezone.utc)  # Only future chunks
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
                    SlotTimeChunk.end_time > datetime.now(timezone.utc)
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
                    reserved_at=datetime.now(timezone.utc)
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
            expiry_time = datetime.now(timezone.utc) - timedelta(minutes=expiry_minutes)
            
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
    
    # Smart chunk system methods
    
    async def create_smart_chunks_batch(
        self, 
        chunks_data: List[Dict[str, Any]]
    ) -> List[SlotTimeChunk]:
        """Create multiple chunks in a single batch operation."""
        try:
            chunks = []
            for chunk_data in chunks_data:
                chunk = SlotTimeChunk(
                    slot_id=chunk_data["slot_id"],
                    start_time=chunk_data["start_time"],
                    end_time=chunk_data["end_time"],
                    chunk_size_minutes=chunk_data["chunk_size_minutes"],
                    demand_level=chunk_data["demand_level"],
                    generation_strategy=chunk_data["generation_strategy"],
                    status=chunk_data.get("status", ChunkStatus.AVAILABLE.value)
                )
                chunks.append(chunk)
                self.session.add(chunk)
            
            await self.session.flush()
            
            logger.info(
                "Created smart chunks batch",
                chunk_count=len(chunks),
                slot_id=chunks[0].slot_id if chunks else None
            )
            
            return chunks
            
        except Exception as e:
            logger.error("Failed to create smart chunks batch", error=str(e))
            raise
    
    async def get_chunks_by_demand_level(
        self, 
        slot_id: UUID, 
        demand_level: DemandLevel,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SlotTimeChunk]:
        """Get chunks filtered by demand level."""
        try:
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.demand_level == demand_level.value
                )
            )
            
            if start_time:
                query = query.where(SlotTimeChunk.start_time >= start_time)
            if end_time:
                query = query.where(SlotTimeChunk.end_time <= end_time)
            
            query = query.order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(
                "Failed to get chunks by demand level",
                slot_id=slot_id,
                demand_level=demand_level.value,
                error=str(e)
            )
            raise
    
    async def get_chunk_utilization_by_size(
        self, 
        slot_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """Get utilization statistics grouped by chunk size."""
        try:
            query = select(
                SlotTimeChunk.chunk_size_minutes,
                SlotTimeChunk.status,
                func.count(SlotTimeChunk.id).label('count')
            ).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time
                )
            ).group_by(
                SlotTimeChunk.chunk_size_minutes,
                SlotTimeChunk.status
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Process results into structured format
            utilization_stats = {}
            
            for row in rows:
                chunk_size = row.chunk_size_minutes
                status = row.status
                count = row.count
                
                if chunk_size not in utilization_stats:
                    utilization_stats[chunk_size] = {
                        "total_chunks": 0,
                        "status_breakdown": {},
                        "utilization_rate": 0.0
                    }
                
                utilization_stats[chunk_size]["status_breakdown"][status] = count
                utilization_stats[chunk_size]["total_chunks"] += count
            
            # Calculate utilization rates
            for chunk_size, stats in utilization_stats.items():
                booked = stats["status_breakdown"].get(ChunkStatus.BOOKED.value, 0)
                reserved = stats["status_breakdown"].get(ChunkStatus.TEMP_RESERVED.value, 0)
                total = stats["total_chunks"]
                
                if total > 0:
                    stats["utilization_rate"] = round((booked + reserved) / total, 3)
            
            return utilization_stats
            
        except Exception as e:
            logger.error(
                "Failed to get chunk utilization by size",
                slot_id=slot_id,
                error=str(e)
            )
            raise
    
    async def optimize_chunk_fragmentation(
        self, 
        slot_id: UUID,
        target_chunk_size: int = 15
    ) -> Dict[str, Any]:
        """Analyze and suggest optimizations for chunk fragmentation."""
        try:
            # Get all available chunks for the slot
            query = select(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.status == ChunkStatus.AVAILABLE.value
                )
            ).order_by(SlotTimeChunk.start_time)
            
            result = await self.session.execute(query)
            chunks = result.scalars().all()
            
            if not chunks:
                return {
                    "fragmentation_score": 0.0,
                    "optimization_suggestions": [],
                    "total_chunks_analyzed": 0
                }
            
            # Analyze fragmentation
            total_chunks = len(chunks)
            small_chunks = sum(1 for chunk in chunks if chunk.chunk_size_minutes < target_chunk_size)
            fragmentation_score = small_chunks / total_chunks if total_chunks > 0 else 0
            
            # Find opportunities for consolidation
            consolidation_opportunities = []
            
            i = 0
            while i < len(chunks) - 1:
                current_chunk = chunks[i]
                next_chunk = chunks[i + 1]
                
                # Check if chunks are adjacent and can be consolidated
                if (current_chunk.end_time == next_chunk.start_time and
                    current_chunk.chunk_size_minutes + next_chunk.chunk_size_minutes <= target_chunk_size):
                    
                    consolidation_opportunities.append({
                        "chunks_to_merge": [current_chunk.id, next_chunk.id],
                        "current_sizes": [current_chunk.chunk_size_minutes, next_chunk.chunk_size_minutes],
                        "consolidated_size": current_chunk.chunk_size_minutes + next_chunk.chunk_size_minutes,
                        "time_range": {
                            "start": current_chunk.start_time.isoformat(),
                            "end": next_chunk.end_time.isoformat()
                        }
                    })
                    
                    i += 2  # Skip the next chunk since we're considering merging it
                else:
                    i += 1
            
            optimization_suggestions = []
            
            if fragmentation_score > 0.3:  # High fragmentation
                optimization_suggestions.append({
                    "type": "reduce_fragmentation",
                    "priority": "high",
                    "description": f"High fragmentation detected ({fragmentation_score:.1%}). Consider consolidating small chunks.",
                    "consolidation_opportunities": len(consolidation_opportunities)
                })
            
            if len(consolidation_opportunities) > 0:
                optimization_suggestions.append({
                    "type": "chunk_consolidation",
                    "priority": "medium",
                    "description": f"Found {len(consolidation_opportunities)} consolidation opportunities",
                    "opportunities": consolidation_opportunities
                })
            
            return {
                "fragmentation_score": round(fragmentation_score, 3),
                "optimization_suggestions": optimization_suggestions,
                "total_chunks_analyzed": total_chunks,
                "small_chunks_count": small_chunks,
                "target_chunk_size": target_chunk_size,
                "consolidation_opportunities": len(consolidation_opportunities)
            }
            
        except Exception as e:
            logger.error(
                "Failed to analyze chunk fragmentation",
                slot_id=slot_id,
                error=str(e)
            )
            raise
    
    async def bulk_update_demand_level(
        self, 
        slot_id: UUID,
        new_demand_level: DemandLevel,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Bulk update demand level for chunks in a time range."""
        try:
            query = update(SlotTimeChunk).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.status == ChunkStatus.AVAILABLE.value
                )
            )
            
            if start_time:
                query = query.where(SlotTimeChunk.start_time >= start_time)
            if end_time:
                query = query.where(SlotTimeChunk.end_time <= end_time)
            
            query = query.values(demand_level=new_demand_level.value)
            
            result = await self.session.execute(query)
            updated_count = result.rowcount
            
            logger.info(
                "Bulk updated demand level",
                slot_id=slot_id,
                new_demand_level=new_demand_level.value,
                updated_count=updated_count
            )
            
            return updated_count
            
        except Exception as e:
            logger.error(
                "Failed to bulk update demand level",
                slot_id=slot_id,
                new_demand_level=new_demand_level.value,
                error=str(e)
            )
            raise
    
    async def get_demand_level_distribution(
        self, 
        slot_id: UUID,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get distribution of chunks by demand level for analysis."""
        try:
            start_time = datetime.now(timezone.utc)
            end_time = start_time + timedelta(hours=time_window_hours)
            
            query = select(
                SlotTimeChunk.demand_level,
                SlotTimeChunk.generation_strategy,
                func.count(SlotTimeChunk.id).label('count'),
                func.sum(SlotTimeChunk.chunk_size_minutes).label('total_minutes')
            ).where(
                and_(
                    SlotTimeChunk.slot_id == slot_id,
                    SlotTimeChunk.start_time >= start_time,
                    SlotTimeChunk.end_time <= end_time
                )
            ).group_by(
                SlotTimeChunk.demand_level,
                SlotTimeChunk.generation_strategy
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            distribution = {}
            total_chunks = 0
            total_minutes = 0
            
            for row in rows:
                demand_level = row.demand_level
                generation_strategy = row.generation_strategy
                count = row.count
                minutes = row.total_minutes or 0
                
                if demand_level not in distribution:
                    distribution[demand_level] = {
                        "chunk_count": 0,
                        "total_minutes": 0,
                        "generation_strategies": {},
                        "percentage": 0.0
                    }
                
                distribution[demand_level]["chunk_count"] += count
                distribution[demand_level]["total_minutes"] += minutes
                distribution[demand_level]["generation_strategies"][generation_strategy] = count
                
                total_chunks += count
                total_minutes += minutes
            
            # Calculate percentages
            for demand_level, stats in distribution.items():
                if total_chunks > 0:
                    stats["percentage"] = round((stats["chunk_count"] / total_chunks) * 100, 2)
            
            return {
                "distribution": distribution,
                "summary": {
                    "total_chunks": total_chunks,
                    "total_minutes": total_minutes,
                    "time_window_hours": time_window_hours,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(
                "Failed to get demand level distribution",
                slot_id=slot_id,
                error=str(e)
            )
            raise
