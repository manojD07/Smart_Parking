"""Test suite for conflict detection and resolution services."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conflict_resolution import (
    ConflictResolutionService, ConflictType, ConflictSeverity, ResolutionStrategy
)
from app.models.parking import VehicleType, SlotStatus
from app.models.booking import BookingStatus
from tests.conftest import create_test_user, create_test_parking_lot, create_test_slot, create_test_booking


class TestConflictDetection:
    """Test conflict detection functionality."""
    
    @pytest.mark.asyncio
    async def test_detect_time_overlap_conflicts(self, async_session: AsyncSession):
        """Test detection of time overlap conflicts."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        # Create existing booking
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        existing_booking = await create_test_booking(
            async_session, user.id, lot.id, slot.id, start_time, end_time
        )
        
        service = ConflictResolutionService(async_session)
        
        # Test overlapping time request
        overlap_start = start_time + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=1)
        
        conflicts = await service.detect_conflicts(
            slot_id=slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=overlap_start,
            end_time=overlap_end
        )
        
        # Assertions
        assert len(conflicts) > 0
        time_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.TIME_OVERLAP]
        assert len(time_conflicts) == 1
        assert time_conflicts[0].severity == ConflictSeverity.CRITICAL
        assert existing_booking.id in time_conflicts[0].conflicting_bookings
    
    @pytest.mark.asyncio
    async def test_detect_capacity_conflicts_bike_in_car(self, async_session: AsyncSession):
        """Test detection of capacity conflicts for bike in car slot."""
        # Setup
        user1 = await create_test_user(async_session)
        user2 = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        car_slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        # Create 2 bike bookings (max capacity)
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        await create_test_booking(
            async_session, user1.id, lot.id, car_slot.id, start_time, end_time, VehicleType.BIKE
        )
        await create_test_booking(
            async_session, user2.id, lot.id, car_slot.id, start_time, end_time, VehicleType.BIKE
        )
        
        service = ConflictResolutionService(async_session)
        
        # Try to add third bike
        conflicts = await service.detect_conflicts(
            slot_id=car_slot.id,
            user_id=user1.id,
            vehicle_type=VehicleType.BIKE.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assertions
        capacity_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.CAPACITY_EXCEEDED]
        assert len(capacity_conflicts) > 0
        assert capacity_conflicts[0].severity == ConflictSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_detect_state_conflicts(self, async_session: AsyncSession):
        """Test detection of slot state conflicts."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR, status=SlotStatus.MAINTENANCE)
        
        service = ConflictResolutionService(async_session)
        
        # Try to book maintenance slot
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        conflicts = await service.detect_conflicts(
            slot_id=slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assertions
        state_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.STATE_CONFLICT]
        assert len(state_conflicts) > 0
        assert state_conflicts[0].severity == ConflictSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_detect_system_constraint_conflicts(self, async_session: AsyncSession):
        """Test detection of system constraint conflicts."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        service = ConflictResolutionService(async_session)
        
        # Test past booking
        past_start = datetime.now(timezone.utc) - timedelta(hours=1)
        past_end = past_start + timedelta(hours=2)
        
        conflicts = await service.detect_conflicts(
            slot_id=slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=past_start,
            end_time=past_end
        )
        
        # Assertions
        system_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.SYSTEM_CONSTRAINT]
        assert len(system_conflicts) > 0
        assert system_conflicts[0].severity == ConflictSeverity.CRITICAL
        assert "past" in system_conflicts[0].description.lower()
    
    @pytest.mark.asyncio
    async def test_detect_user_limit_conflicts(self, async_session: AsyncSession):
        """Test detection of user booking limit conflicts."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        
        service = ConflictResolutionService(async_session)
        
        # Create multiple bookings for user (exceed limit)
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # Create max allowed bookings
        for i in range(service.max_user_concurrent_bookings):
            slot = await create_test_slot(async_session, lot.id, VehicleType.CAR, number=i+1)
            await create_test_booking(
                async_session, user.id, lot.id, slot.id, 
                start_time + timedelta(minutes=i*30), 
                end_time + timedelta(minutes=i*30)
            )
        
        # Try to create one more
        extra_slot = await create_test_slot(async_session, lot.id, VehicleType.CAR, number=99)
        conflicts = await service.detect_conflicts(
            slot_id=extra_slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assertions
        user_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.USER_LIMIT_EXCEEDED]
        assert len(user_conflicts) > 0
        assert user_conflicts[0].severity == ConflictSeverity.MEDIUM


class TestConflictResolution:
    """Test conflict resolution functionality."""
    
    @pytest.mark.asyncio
    async def test_resolve_no_conflicts(self, async_session: AsyncSession):
        """Test resolving when no conflicts exist."""
        service = ConflictResolutionService(async_session)
        
        result = await service.resolve_conflicts(conflicts=[])
        
        # Assertions
        assert result.success is True
        assert result.strategy_used == ResolutionStrategy.AUTO_RESOLVE
    
    @pytest.mark.asyncio
    async def test_resolve_critical_conflicts(self, async_session: AsyncSession):
        """Test resolving critical conflicts."""
        # Setup critical conflict
        from app.services.conflict_resolution import ConflictDetails
        
        critical_conflict = ConflictDetails(
            conflict_id="test_critical",
            conflict_type=ConflictType.TIME_OVERLAP,
            severity=ConflictSeverity.CRITICAL,
            description="Critical time overlap",
            affected_resources=["slot_123"],
            conflicting_bookings=[uuid4()],
            resolution_strategies=[ResolutionStrategy.BLOCK],
            auto_resolvable=False,
            estimated_resolution_time=None,
            metadata={}
        )
        
        service = ConflictResolutionService(async_session)
        result = await service.resolve_conflicts(conflicts=[critical_conflict])
        
        # Assertions
        assert result.success is False
        assert result.strategy_used == ResolutionStrategy.BLOCK
        assert len(result.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_resolve_with_alternative_strategy(self, async_session: AsyncSession):
        """Test resolving with alternative slot strategy."""
        # Setup resolvable conflict
        from app.services.conflict_resolution import ConflictDetails
        
        resolvable_conflict = ConflictDetails(
            conflict_id="test_resolvable",
            conflict_type=ConflictType.CAPACITY_EXCEEDED,
            severity=ConflictSeverity.HIGH,
            description="Capacity exceeded",
            affected_resources=["slot_123"],
            conflicting_bookings=[],
            resolution_strategies=[ResolutionStrategy.ALTERNATIVE_SLOT],
            auto_resolvable=True,
            estimated_resolution_time=timedelta(seconds=10),
            metadata={}
        )
        
        service = ConflictResolutionService(async_session)
        result = await service.resolve_conflicts(
            conflicts=[resolvable_conflict],
            preferred_strategy=ResolutionStrategy.ALTERNATIVE_SLOT
        )
        
        # Assertions
        assert result.success is True
        assert result.strategy_used == ResolutionStrategy.ALTERNATIVE_SLOT
        assert len(result.alternative_suggestions) > 0


class TestAtomicValidation:
    """Test atomic booking validation functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_booking_atomically_success(self, async_session: AsyncSession):
        """Test successful atomic booking validation."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        service = ConflictResolutionService(async_session)
        
        # Test valid booking
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        is_valid, conflicts, resolution_result = await service.validate_booking_atomically(
            slot_id=slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assertions
        assert is_valid is True
        assert len(conflicts) == 0
        assert resolution_result is None
    
    @pytest.mark.asyncio
    async def test_validate_booking_atomically_conflicts(self, async_session: AsyncSession):
        """Test atomic booking validation with conflicts."""
        # Setup
        user = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        # Create existing booking
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        await create_test_booking(
            async_session, user.id, lot.id, slot.id, start_time, end_time
        )
        
        service = ConflictResolutionService(async_session)
        
        # Test conflicting booking
        overlap_start = start_time + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=1)
        
        is_valid, conflicts, resolution_result = await service.validate_booking_atomically(
            slot_id=slot.id,
            user_id=user.id,
            vehicle_type=VehicleType.CAR.value,
            start_time=overlap_start,
            end_time=overlap_end
        )
        
        # Assertions
        assert is_valid is False
        assert len(conflicts) > 0
        assert resolution_result is not None
        assert resolution_result.success is False


class TestConflictResolutionIntegration:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_bike_car_slot_conflict_resolution(self, async_session: AsyncSession):
        """Test comprehensive bike-in-car slot conflict resolution."""
        # Setup
        user1 = await create_test_user(async_session)
        user2 = await create_test_user(async_session)
        user3 = await create_test_user(async_session)
        lot = await create_test_parking_lot(async_session)
        car_slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        service = ConflictResolutionService(async_session)
        
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # First bike: should succeed
        is_valid1, conflicts1, _ = await service.validate_booking_atomically(
            slot_id=car_slot.id,
            user_id=user1.id,
            vehicle_type=VehicleType.BIKE.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create first bike booking
        if is_valid1:
            await create_test_booking(
                async_session, user1.id, lot.id, car_slot.id, start_time, end_time, VehicleType.BIKE
            )
        
        # Second bike: should succeed
        is_valid2, conflicts2, _ = await service.validate_booking_atomically(
            slot_id=car_slot.id,
            user_id=user2.id,
            vehicle_type=VehicleType.BIKE.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create second bike booking
        if is_valid2:
            await create_test_booking(
                async_session, user2.id, lot.id, car_slot.id, start_time, end_time, VehicleType.BIKE
            )
        
        # Third bike: should fail
        is_valid3, conflicts3, resolution3 = await service.validate_booking_atomically(
            slot_id=car_slot.id,
            user_id=user3.id,
            vehicle_type=VehicleType.BIKE.value,
            start_time=start_time,
            end_time=end_time
        )
        
        # Assertions
        assert is_valid1 is True
        assert is_valid2 is True
        assert is_valid3 is False
        
        capacity_conflicts = [c for c in conflicts3 if c.conflict_type == ConflictType.CAPACITY_EXCEEDED]
        assert len(capacity_conflicts) > 0
        
        # Check alternative suggestions
        if resolution3:
            assert len(resolution3.alternative_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_booking_simulation(self, async_session: AsyncSession):
        """Test simulation of concurrent booking attempts."""
        # Setup
        users = [await create_test_user(async_session) for _ in range(3)]
        lot = await create_test_parking_lot(async_session)
        slot = await create_test_slot(async_session, lot.id, VehicleType.CAR)
        
        service = ConflictResolutionService(async_session)
        
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # Simulate concurrent validation attempts
        validation_results = []
        for user in users:
            is_valid, conflicts, resolution_result = await service.validate_booking_atomically(
                slot_id=slot.id,
                user_id=user.id,
                vehicle_type=VehicleType.CAR.value,
                start_time=start_time,
                end_time=end_time
            )
            validation_results.append((is_valid, conflicts, resolution_result))
        
        # Assertions
        valid_results = [r for r in validation_results if r[0] is True]
        assert len(valid_results) >= 1  # At least one should succeed
        
        invalid_results = [r for r in validation_results if r[0] is False]
        # Some should fail due to conflicts if multiple users attempt same slot
        if len(invalid_results) > 0:
            for _, conflicts, _ in invalid_results:
                assert len(conflicts) > 0


# Helper functions for testing
async def create_test_booking(
    session: AsyncSession,
    user_id,
    lot_id,
    slot_id,
    start_time,
    end_time,
    vehicle_type=VehicleType.CAR
):
    """Create a test booking."""
    from app.models.booking import Booking
    
    booking = Booking(
        user_id=user_id,
        lot_id=lot_id,
        slot_id=slot_id,
        vehicle_type=vehicle_type.value,
        vehicle_number="TEST123",
        start_time=start_time,
        end_time=end_time,
        total_amount=50.00,
        booking_reference=f"TEST{uuid4().hex[:8].upper()}",
        status=BookingStatus.CONFIRMED.value
    )
    
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking
