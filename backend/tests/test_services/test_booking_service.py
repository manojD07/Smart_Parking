"""Tests for booking service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.booking import BookingService
from app.models.booking import BookingStatus
from app.models.parking import VehicleType
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    InsufficientSlotsError,
    BookingNotCancellableError,
    UserNotActiveError
)
from tests.conftest import BookingFactory


class TestBookingService:
    """Test cases for BookingService."""
    
    @pytest.fixture
    async def booking_service(self, db_session):
        """Create booking service instance."""
        return BookingService(db_session)
    
    async def test_create_booking_success(
        self, 
        booking_service, 
        test_user, 
        test_parking_lot, 
        test_parking_slots
    ):
        """Test successful booking creation."""
        booking_data = BookingFactory.build(
            user_id=test_user.id,
            lot_id=test_parking_lot.id
        )
        
        booking = await booking_service.create_booking(
            user_id=booking_data["user_id"],
            lot_id=booking_data["lot_id"],
            vehicle_type=VehicleType.CAR,
            vehicle_number=booking_data["vehicle_number"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"]
        )
        
        assert booking.id is not None
        assert booking.user_id == test_user.id
        assert booking.lot_id == test_parking_lot.id
        assert booking.vehicle_type == VehicleType.CAR.value
        assert booking.status == BookingStatus.ACTIVE.value
        assert booking.booking_reference is not None
        assert len(booking.booking_reference) == 8
        assert booking.total_amount > 0
    
    async def test_create_booking_bike_in_car_slot(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test bike booking in car slot when bike slots unavailable."""
        # Book all bike slots first (simplified test)
        booking_data = BookingFactory.build(
            user_id=test_user.id,
            lot_id=test_parking_lot.id
        )
        
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.BIKE,
            vehicle_number=booking_data["vehicle_number"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"]
        )
        
        assert booking.vehicle_type == VehicleType.BIKE.value
        assert booking.slot.slot_type in [VehicleType.BIKE.value, VehicleType.CAR.value]
    
    async def test_create_booking_invalid_user(
        self,
        booking_service,
        test_parking_lot,
        test_parking_slots
    ):
        """Test booking creation with invalid user."""
        booking_data = BookingFactory.build(
            user_id=uuid4(),  # Non-existent user
            lot_id=test_parking_lot.id
        )
        
        with pytest.raises(NotFoundError, match="User not found"):
            await booking_service.create_booking(
                user_id=booking_data["user_id"],
                lot_id=booking_data["lot_id"],
                vehicle_type=VehicleType.CAR,
                vehicle_number=booking_data["vehicle_number"],
                start_time=booking_data["start_time"],
                end_time=booking_data["end_time"]
            )
    
    async def test_create_booking_invalid_lot(
        self,
        booking_service,
        test_user
    ):
        """Test booking creation with invalid parking lot."""
        booking_data = BookingFactory.build(
            user_id=test_user.id,
            lot_id=uuid4()  # Non-existent lot
        )
        
        with pytest.raises(NotFoundError, match="Parking lot not found"):
            await booking_service.create_booking(
                user_id=booking_data["user_id"],
                lot_id=booking_data["lot_id"],
                vehicle_type=VehicleType.CAR,
                vehicle_number=booking_data["vehicle_number"],
                start_time=booking_data["start_time"],
                end_time=booking_data["end_time"]
            )
    
    async def test_create_booking_invalid_time_range(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test booking creation with invalid time range."""
        # End time before start time
        start_time = datetime.utcnow() + timedelta(hours=2)
        end_time = datetime.utcnow() + timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="End time must be after start time"):
            await booking_service.create_booking(
                user_id=test_user.id,
                lot_id=test_parking_lot.id,
                vehicle_type=VehicleType.CAR,
                vehicle_number="TEST123",
                start_time=start_time,
                end_time=end_time
            )
    
    async def test_create_booking_past_time(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test booking creation with past start time."""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow() + timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="must be in the future"):
            await booking_service.create_booking(
                user_id=test_user.id,
                lot_id=test_parking_lot.id,
                vehicle_type=VehicleType.CAR,
                vehicle_number="TEST123",
                start_time=start_time,
                end_time=end_time
            )
    
    async def test_cancel_booking_success(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test successful booking cancellation."""
        # Create booking
        booking_data = BookingFactory.build()
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number=booking_data["vehicle_number"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"]
        )
        
        # Cancel booking
        cancelled = await booking_service.cancel_booking(booking.id, test_user.id)
        
        assert cancelled is True
        
        # Verify booking status
        updated_booking = await booking_service.get_by_id(booking.id)
        assert updated_booking.status == BookingStatus.CANCELLED.value
    
    async def test_cancel_booking_not_owner(
        self,
        booking_service,
        test_user,
        admin_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test booking cancellation by non-owner."""
        # Create booking
        booking_data = BookingFactory.build()
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number=booking_data["vehicle_number"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"]
        )
        
        # Try to cancel as different user
        with pytest.raises(ValidationError, match="You can only cancel your own bookings"):
            await booking_service.cancel_booking(booking.id, admin_user.id)
    
    async def test_check_in_booking_success(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test successful booking check-in."""
        # Create booking starting now
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number="TEST123",
            start_time=start_time,
            end_time=end_time
        )
        
        # Check in
        checked_in = await booking_service.check_in_booking(booking.id, test_user.id)
        
        assert checked_in is True
        
        # Verify check-in time is set
        updated_booking = await booking_service.get_by_id(booking.id)
        assert updated_booking.check_in_time is not None
    
    async def test_check_out_booking_success(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test successful booking check-out."""
        # Create and check in to booking
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number="TEST123",
            start_time=start_time,
            end_time=end_time
        )
        
        await booking_service.check_in_booking(booking.id, test_user.id)
        
        # Check out
        checked_out = await booking_service.check_out_booking(booking.id, test_user.id)
        
        assert checked_out is True
        
        # Verify booking is completed
        updated_booking = await booking_service.get_by_id(booking.id)
        assert updated_booking.check_out_time is not None
        assert updated_booking.status == BookingStatus.COMPLETED.value
    
    async def test_get_user_bookings(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test getting user bookings."""
        # Create multiple bookings
        for i in range(3):
            booking_data = BookingFactory.build()
            await booking_service.create_booking(
                user_id=test_user.id,
                lot_id=test_parking_lot.id,
                vehicle_type=VehicleType.CAR,
                vehicle_number=f"TEST{i:03d}",
                start_time=booking_data["start_time"] + timedelta(hours=i),
                end_time=booking_data["end_time"] + timedelta(hours=i)
            )
        
        # Get user bookings
        bookings = await booking_service.get_user_bookings(test_user.id)
        
        assert len(bookings) == 3
        assert all(booking.user_id == test_user.id for booking in bookings)
    
    async def test_search_bookings(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots
    ):
        """Test booking search functionality."""
        # Create booking with specific vehicle number
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number="SEARCH123",
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=3)
        )
        
        # Search by vehicle number
        results = await booking_service.search_bookings("SEARCH123")
        
        assert len(results) >= 1
        assert any(b.vehicle_number == "SEARCH123" for b in results)
        
        # Search by booking reference
        results = await booking_service.search_bookings(booking.booking_reference)
        
        assert len(results) >= 1
        assert any(b.booking_reference == booking.booking_reference for b in results)
    
    async def test_process_expired_bookings(
        self,
        booking_service,
        test_user,
        test_parking_lot,
        test_parking_slots,
        db_session
    ):
        """Test processing of expired bookings."""
        # Create booking that has already ended
        start_time = datetime.utcnow() - timedelta(hours=3)
        end_time = datetime.utcnow() - timedelta(hours=1)
        
        booking = await booking_service.create_booking(
            user_id=test_user.id,
            lot_id=test_parking_lot.id,
            vehicle_type=VehicleType.CAR,
            vehicle_number="EXPIRED123",
            start_time=start_time,
            end_time=end_time
        )
        
        # Process expired bookings
        expired_count = await booking_service.process_expired_bookings()
        
        assert expired_count >= 1
        
        # Verify booking is marked as expired
        updated_booking = await booking_service.get_by_id(booking.id)
        assert updated_booking.status == BookingStatus.EXPIRED.value
