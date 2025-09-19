"""
Smart Chunk Manager for Dynamic Chunk Generation

Intelligently creates and manages chunks based on:
- Demand levels (low/medium/high/peak)
- Booking patterns and conflicts
- Space utilization optimization
- Revenue maximization strategies
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot_chunks import SlotTimeChunk, DemandLevel, GenerationStrategy, ChunkStatus
from app.models.parking import ParkingSlot
from app.services.hybrid_duration_calculator import duration_calculator
from app.core.config import get_settings
from app.core.cache import cache_manager

logger = structlog.get_logger(__name__)


class ChunkGenerationMode(str, Enum):
    """Chunk generation modes for different scenarios."""
    DEMAND_OPTIMIZED = "demand_optimized"
    REVENUE_OPTIMIZED = "revenue_optimized"
    SPACE_OPTIMIZED = "space_optimized"
    CONFLICT_MINIMIZED = "conflict_minimized"
    HYBRID = "hybrid"


@dataclass
class ChunkGenerationRequest:
    """Request for chunk generation."""
    slot_id: UUID
    start_time: datetime
    end_time: datetime
    demand_level: DemandLevel
    generation_mode: ChunkGenerationMode = ChunkGenerationMode.HYBRID
    target_booking_duration: Optional[int] = None
    existing_chunks: List[SlotTimeChunk] = None
    
    def __post_init__(self):
        if self.existing_chunks is None:
            self.existing_chunks = []


@dataclass
class ChunkGenerationResult:
    """Result of chunk generation."""
    generated_chunks: List[Dict]
    total_chunks: int
    coverage_minutes: int
    efficiency_score: float
    conflict_probability: float
    revenue_optimization_score: float
    metadata: Dict
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class SmartChunkManager:
    """
    Intelligent chunk generation and management system.
    
    Generates optimal chunks based on demand levels, booking patterns,
    and business optimization strategies.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize smart chunk manager."""
        self.session = session
        from app.core.config import settings
        self.settings = settings
        self.duration_calculator = duration_calculator
        self.logger = logger.bind(service="SmartChunkManager")
        
        # Chunk size strategies by demand level
        self.demand_chunk_strategies = {
            DemandLevel.LOW: {
                "primary_chunk_size": 30,
                "secondary_chunk_size": 15,
                "micro_chunk_threshold": 0.1,  # 10% micro chunks
                "generation_strategy": GenerationStrategy.AUTO
            },
            DemandLevel.MEDIUM: {
                "primary_chunk_size": 15,
                "secondary_chunk_size": 5,
                "micro_chunk_threshold": 0.2,  # 20% micro chunks
                "generation_strategy": GenerationStrategy.AUTO
            },
            DemandLevel.HIGH: {
                "primary_chunk_size": 5,
                "secondary_chunk_size": 1,
                "micro_chunk_threshold": 0.4,  # 40% micro chunks
                "generation_strategy": GenerationStrategy.DEMAND_BASED
            },
            DemandLevel.PEAK: {
                "primary_chunk_size": 1,
                "secondary_chunk_size": 1,
                "micro_chunk_threshold": 1.0,  # 100% micro chunks
                "generation_strategy": GenerationStrategy.DEMAND_BASED
            }
        }
    
    async def generate_chunks_for_slot(
        self, 
        request: ChunkGenerationRequest
    ) -> ChunkGenerationResult:
        """
        Generate optimal chunks for a parking slot time range.
        
        Args:
            request: Chunk generation request with parameters
            
        Returns:
            ChunkGenerationResult with generated chunks and metadata
        """
        try:
            self.logger.info(
                "Starting smart chunk generation",
                slot_id=request.slot_id,
                start_time=request.start_time.isoformat(),
                end_time=request.end_time.isoformat(),
                demand_level=request.demand_level.value,
                generation_mode=request.generation_mode.value
            )
            
            # Validate request
            if request.start_time >= request.end_time:
                raise ValueError("Start time must be before end time")
            
            # Calculate total time window
            total_minutes = int((request.end_time - request.start_time).total_seconds() / 60)
            
            # Generate chunks based on demand level and mode
            if request.generation_mode == ChunkGenerationMode.DEMAND_OPTIMIZED:
                chunks = await self._generate_demand_optimized_chunks(request, total_minutes)
            elif request.generation_mode == ChunkGenerationMode.REVENUE_OPTIMIZED:
                chunks = await self._generate_revenue_optimized_chunks(request, total_minutes)
            elif request.generation_mode == ChunkGenerationMode.SPACE_OPTIMIZED:
                chunks = await self._generate_space_optimized_chunks(request, total_minutes)
            elif request.generation_mode == ChunkGenerationMode.CONFLICT_MINIMIZED:
                chunks = await self._generate_conflict_minimized_chunks(request, total_minutes)
            else:  # HYBRID mode
                chunks = await self._generate_hybrid_chunks(request, total_minutes)
            
            # Calculate performance metrics
            efficiency_score = self._calculate_efficiency_score(chunks, total_minutes)
            conflict_probability = self._calculate_conflict_probability(chunks, request)
            revenue_score = self._calculate_revenue_optimization_score(chunks, request)
            
            # Generate metadata
            metadata = {
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_time_window_minutes": total_minutes,
                "demand_level": request.demand_level.value,
                "generation_mode": request.generation_mode.value,
                "chunk_size_distribution": self._analyze_chunk_distribution(chunks),
                "optimization_metrics": {
                    "efficiency": efficiency_score,
                    "conflict_probability": conflict_probability,
                    "revenue_optimization": revenue_score
                }
            }
            
            result = ChunkGenerationResult(
                generated_chunks=chunks,
                total_chunks=len(chunks),
                coverage_minutes=sum(chunk["chunk_size_minutes"] for chunk in chunks),
                efficiency_score=efficiency_score,
                conflict_probability=conflict_probability,
                revenue_optimization_score=revenue_score,
                metadata=metadata
            )
            
            self.logger.info(
                "Smart chunk generation completed",
                slot_id=request.slot_id,
                total_chunks=result.total_chunks,
                efficiency_score=result.efficiency_score,
                conflict_probability=result.conflict_probability
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Error generating smart chunks",
                slot_id=request.slot_id,
                error=str(e)
            )
            raise
    
    async def _generate_demand_optimized_chunks(
        self, 
        request: ChunkGenerationRequest, 
        total_minutes: int
    ) -> List[Dict]:
        """Generate chunks optimized for current demand level."""
        chunks = []
        strategy = self.demand_chunk_strategies[request.demand_level]
        
        current_time = request.start_time
        primary_size = strategy["primary_chunk_size"]
        secondary_size = strategy["secondary_chunk_size"]
        micro_threshold = strategy["micro_chunk_threshold"]
        
        chunk_count = 0
        total_chunks_needed = total_minutes // primary_size
        
        while current_time < request.end_time:
            remaining_minutes = int((request.end_time - current_time).total_seconds() / 60)
            
            # Determine chunk size based on demand strategy
            if chunk_count / max(total_chunks_needed, 1) < micro_threshold:
                # Use smaller chunks for high-precision booking
                chunk_size = min(secondary_size, remaining_minutes)
            else:
                # Use primary chunk size
                chunk_size = min(primary_size, remaining_minutes)
            
            if chunk_size <= 0:
                break
            
            chunk_end = current_time + timedelta(minutes=chunk_size)
            
            chunks.append({
                "slot_id": request.slot_id,
                "start_time": current_time,
                "end_time": chunk_end,
                "chunk_size_minutes": chunk_size,
                "demand_level": request.demand_level.value,
                "generation_strategy": strategy["generation_strategy"].value,
                "status": ChunkStatus.AVAILABLE.value
            })
            
            current_time = chunk_end
            chunk_count += 1
        
        return chunks
    
    async def _generate_revenue_optimized_chunks(
        self, 
        request: ChunkGenerationRequest, 
        total_minutes: int
    ) -> List[Dict]:
        """Generate chunks optimized for maximum revenue."""
        chunks = []
        
        # Revenue optimization: Create chunks that align with popular booking durations
        popular_durations = [15, 30, 60, 90, 120]  # Most common booking durations
        
        current_time = request.start_time
        
        while current_time < request.end_time:
            remaining_minutes = int((request.end_time - current_time).total_seconds() / 60)
            
            # Find the largest popular duration that fits
            chunk_size = 5  # Default fallback
            for duration in reversed(popular_durations):
                if duration <= remaining_minutes:
                    chunk_size = duration
                    break
            
            # If no popular duration fits, use remaining time
            if chunk_size > remaining_minutes:
                chunk_size = remaining_minutes
            
            if chunk_size <= 0:
                break
            
            chunk_end = current_time + timedelta(minutes=chunk_size)
            
            chunks.append({
                "slot_id": request.slot_id,
                "start_time": current_time,
                "end_time": chunk_end,
                "chunk_size_minutes": chunk_size,
                "demand_level": request.demand_level.value,
                "generation_strategy": GenerationStrategy.AUTO.value,
                "status": ChunkStatus.AVAILABLE.value
            })
            
            current_time = chunk_end
        
        return chunks
    
    async def _generate_space_optimized_chunks(
        self, 
        request: ChunkGenerationRequest, 
        total_minutes: int
    ) -> List[Dict]:
        """Generate chunks optimized for space utilization."""
        chunks = []
        
        # Space optimization: Use uniform chunk sizes for predictable packing
        optimal_chunk_size = self._calculate_optimal_uniform_size(total_minutes)
        
        current_time = request.start_time
        
        while current_time < request.end_time:
            remaining_minutes = int((request.end_time - current_time).total_seconds() / 60)
            chunk_size = min(optimal_chunk_size, remaining_minutes)
            
            if chunk_size <= 0:
                break
            
            chunk_end = current_time + timedelta(minutes=chunk_size)
            
            chunks.append({
                "slot_id": request.slot_id,
                "start_time": current_time,
                "end_time": chunk_end,
                "chunk_size_minutes": chunk_size,
                "demand_level": request.demand_level.value,
                "generation_strategy": GenerationStrategy.AUTO.value,
                "status": ChunkStatus.AVAILABLE.value
            })
            
            current_time = chunk_end
        
        return chunks
    
    async def _generate_conflict_minimized_chunks(
        self, 
        request: ChunkGenerationRequest, 
        total_minutes: int
    ) -> List[Dict]:
        """Generate chunks that minimize booking conflicts."""
        chunks = []
        
        # Conflict minimization: Use 1-minute precision chunks for maximum flexibility
        current_time = request.start_time
        
        while current_time < request.end_time:
            chunk_end = current_time + timedelta(minutes=1)
            
            if chunk_end > request.end_time:
                chunk_end = request.end_time
            
            chunk_size = int((chunk_end - current_time).total_seconds() / 60)
            
            if chunk_size <= 0:
                break
            
            chunks.append({
                "slot_id": request.slot_id,
                "start_time": current_time,
                "end_time": chunk_end,
                "chunk_size_minutes": chunk_size,
                "demand_level": request.demand_level.value,
                "generation_strategy": GenerationStrategy.DEMAND_BASED.value,
                "status": ChunkStatus.AVAILABLE.value
            })
            
            current_time = chunk_end
        
        return chunks
    
    async def _generate_hybrid_chunks(
        self, 
        request: ChunkGenerationRequest, 
        total_minutes: int
    ) -> List[Dict]:
        """Generate chunks using hybrid optimization strategy."""
        chunks = []
        
        # Hybrid approach: Combine demand optimization with revenue considerations
        strategy = self.demand_chunk_strategies[request.demand_level]
        primary_size = strategy["primary_chunk_size"]
        
        # Adjust for target booking duration if provided
        if request.target_booking_duration:
            # Create chunks that align well with target duration
            tier = self.duration_calculator.get_tier_for_duration(request.target_booking_duration)
            if tier:
                increment = self.duration_calculator._get_increment_for_duration(request.target_booking_duration)
                primary_size = increment
        
        current_time = request.start_time
        
        while current_time < request.end_time:
            remaining_minutes = int((request.end_time - current_time).total_seconds() / 60)
            
            # Use adaptive chunk sizing
            chunk_size = min(primary_size, remaining_minutes)
            
            # Ensure minimum chunk size
            if chunk_size < 1:
                chunk_size = 1
            
            if chunk_size <= 0:
                break
            
            chunk_end = current_time + timedelta(minutes=chunk_size)
            
            chunks.append({
                "slot_id": request.slot_id,
                "start_time": current_time,
                "end_time": chunk_end,
                "chunk_size_minutes": chunk_size,
                "demand_level": request.demand_level.value,
                "generation_strategy": strategy["generation_strategy"].value,
                "status": ChunkStatus.AVAILABLE.value
            })
            
            current_time = chunk_end
        
        return chunks
    
    def _calculate_optimal_uniform_size(self, total_minutes: int) -> int:
        """Calculate optimal uniform chunk size for space utilization."""
        # Find chunk size that minimizes waste
        possible_sizes = [1, 5, 10, 15, 30]
        best_size = 15  # Default
        min_waste = float('inf')
        
        for size in possible_sizes:
            waste = total_minutes % size
            if waste < min_waste:
                min_waste = waste
                best_size = size
        
        return best_size
    
    def _calculate_efficiency_score(self, chunks: List[Dict], total_minutes: int) -> float:
        """Calculate efficiency score for chunk distribution."""
        if not chunks:
            return 0.0
        
        coverage = sum(chunk["chunk_size_minutes"] for chunk in chunks)
        coverage_ratio = coverage / total_minutes if total_minutes > 0 else 0
        
        # Penalty for too many small chunks (overhead)
        small_chunk_penalty = sum(1 for chunk in chunks if chunk["chunk_size_minutes"] <= 2) / len(chunks)
        
        # Reward for good size distribution
        size_variety = len(set(chunk["chunk_size_minutes"] for chunk in chunks))
        variety_bonus = min(size_variety / 5, 0.2)  # Up to 20% bonus
        
        efficiency = (coverage_ratio * 0.7) + variety_bonus - (small_chunk_penalty * 0.3)
        return min(max(efficiency, 0.0), 1.0)
    
    def _calculate_conflict_probability(self, chunks: List[Dict], request: ChunkGenerationRequest) -> float:
        """Calculate probability of booking conflicts."""
        if not chunks:
            return 1.0
        
        # Smaller chunks = lower conflict probability
        avg_chunk_size = sum(chunk["chunk_size_minutes"] for chunk in chunks) / len(chunks)
        
        # Base probability based on chunk size
        base_probability = min(avg_chunk_size / 30, 1.0)
        
        # Adjust for demand level
        demand_multipliers = {
            DemandLevel.LOW: 0.3,
            DemandLevel.MEDIUM: 0.5,
            DemandLevel.HIGH: 0.7,
            DemandLevel.PEAK: 0.9
        }
        
        return base_probability * demand_multipliers.get(request.demand_level, 0.5)
    
    def _calculate_revenue_optimization_score(self, chunks: List[Dict], request: ChunkGenerationRequest) -> float:
        """Calculate revenue optimization score."""
        if not chunks:
            return 0.0
        
        # Score based on alignment with popular booking durations
        popular_durations = {15: 0.3, 30: 0.4, 60: 0.2, 90: 0.05, 120: 0.05}
        
        score = 0.0
        for chunk in chunks:
            chunk_size = chunk["chunk_size_minutes"]
            if chunk_size in popular_durations:
                score += popular_durations[chunk_size]
            elif chunk_size % 15 == 0:  # Divisible by 15
                score += 0.1
            elif chunk_size % 5 == 0:   # Divisible by 5
                score += 0.05
        
        return min(score / len(chunks), 1.0)
    
    def _analyze_chunk_distribution(self, chunks: List[Dict]) -> Dict:
        """Analyze chunk size distribution."""
        if not chunks:
            return {}
        
        size_counts = {}
        total_chunks = len(chunks)
        
        for chunk in chunks:
            size = chunk["chunk_size_minutes"]
            size_counts[size] = size_counts.get(size, 0) + 1
        
        distribution = {
            size: {
                "count": count,
                "percentage": round((count / total_chunks) * 100, 2)
            }
            for size, count in size_counts.items()
        }
        
        return {
            "size_distribution": distribution,
            "avg_chunk_size": sum(chunk["chunk_size_minutes"] for chunk in chunks) / total_chunks,
            "min_chunk_size": min(chunk["chunk_size_minutes"] for chunk in chunks),
            "max_chunk_size": max(chunk["chunk_size_minutes"] for chunk in chunks),
            "unique_sizes": len(size_counts)
        }
    
    async def optimize_existing_chunks(
        self, 
        slot_id: UUID, 
        demand_level: DemandLevel
    ) -> ChunkGenerationResult:
        """Optimize existing chunks based on current demand level."""
        # This would fetch existing chunks and re-optimize them
        # Implementation would involve database queries and chunk reorganization
        pass
    
    async def generate_chunks_for_booking_duration(
        self,
        slot_id: UUID,
        start_time: datetime,
        duration_minutes: int,
        demand_level: DemandLevel = DemandLevel.MEDIUM
    ) -> List[Dict]:
        """Generate precise chunks for a specific booking duration."""
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Use conflict-minimized mode for precise booking chunks
        request = ChunkGenerationRequest(
            slot_id=slot_id,
            start_time=start_time,
            end_time=end_time,
            demand_level=demand_level,
            generation_mode=ChunkGenerationMode.CONFLICT_MINIMIZED,
            target_booking_duration=duration_minutes
        )
        
        result = await self.generate_chunks_for_slot(request)
        return result.generated_chunks


# Global instance for application use
def create_smart_chunk_manager(session: AsyncSession) -> SmartChunkManager:
    """Factory function to create SmartChunkManager instance."""
    return SmartChunkManager(session)
