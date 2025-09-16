"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from uuid import uuid4

from app.core.database import Base, get_async_session
from app.core.config import Settings
from app.main import app
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.models.booking import Booking
from app.services.auth import AuthService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.rollback()
        finally:
            await session.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        redis_url="redis://localhost:6379/15",  # Test Redis DB
        secret_key="test-secret-key",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        environment="testing"
    )


@pytest.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    """Create auth service for tests."""
    return AuthService(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession, auth_service: AuthService) -> User:
    """Create test user."""
    user = await auth_service.register_user(
        email="test@example.com",
        password="TestPassword123",
        first_name="Test",
        last_name="User",
        phone="+1234567890"
    )
    await db_session.commit()
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, auth_service: AuthService) -> User:
    """Create admin test user."""
    user = await auth_service.register_user(
        email="admin@example.com",
        password="AdminPassword123",
        first_name="Admin",
        last_name="User"
    )
    # Make user admin
    user.is_admin = True
    await db_session.commit()
    return user


@pytest.fixture
async def test_parking_lot(db_session: AsyncSession) -> ParkingLot:
    """Create test parking lot."""
    lot = ParkingLot(
        id=uuid4(),
        name="Test Parking Lot",
        address="123 Test Street, Test City",
        latitude=40.7589,
        longitude=-73.9851,
        total_car_slots=50,
        total_bike_slots=20,
        hourly_rate_car=5.00,
        hourly_rate_bike=2.00,
        is_active=True
    )
    db_session.add(lot)
    await db_session.commit()
    await db_session.refresh(lot)
    return lot


@pytest.fixture
async def test_parking_slots(db_session: AsyncSession, test_parking_lot: ParkingLot) -> list[ParkingSlot]:
    """Create test parking slots."""
    slots = []
    
    # Create car slots
    for i in range(10):
        slot = ParkingSlot(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            slot_number=f"C{i+1:03d}",
            slot_type=VehicleType.CAR.value,
            status="available"
        )
        slots.append(slot)
        db_session.add(slot)
    
    # Create bike slots
    for i in range(5):
        slot = ParkingSlot(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            slot_number=f"B{i+1:03d}",
            slot_type=VehicleType.BIKE.value,
            status="available"
        )
        slots.append(slot)
        db_session.add(slot)
    
    await db_session.commit()
    for slot in slots:
        await db_session.refresh(slot)
    
    return slots


@pytest.fixture
async def user_auth_headers(test_user: User, auth_service: AuthService) -> dict[str, str]:
    """Create authorization headers for test user."""
    access_token = auth_service.create_access_token(test_user)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_auth_headers(admin_user: User, auth_service: AuthService) -> dict[str, str]:
    """Create authorization headers for admin user."""
    access_token = auth_service.create_access_token(admin_user)
    return {"Authorization": f"Bearer {access_token}"}


# Test data factories

class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def build(**kwargs) -> dict:
        """Build user data."""
        default_data = {
            "email": f"user{uuid4().hex[:8]}@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        default_data.update(kwargs)
        return default_data


class ParkingLotFactory:
    """Factory for creating test parking lots."""
    
    @staticmethod
    def build(**kwargs) -> dict:
        """Build parking lot data."""
        default_data = {
            "name": f"Test Lot {uuid4().hex[:8]}",
            "address": "123 Test Street, Test City",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "total_car_slots": 50,
            "total_bike_slots": 20,
            "hourly_rate_car": 5.00,
            "hourly_rate_bike": 2.00,
            "is_active": True
        }
        default_data.update(kwargs)
        return default_data


class BookingFactory:
    """Factory for creating test bookings."""
    
    @staticmethod
    def build(**kwargs) -> dict:
        """Build booking data."""
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        default_data = {
            "vehicle_type": VehicleType.CAR.value,
            "vehicle_number": f"TEST{uuid4().hex[:4].upper()}",
            "start_time": start_time,
            "end_time": end_time
        }
        default_data.update(kwargs)
        return default_data
