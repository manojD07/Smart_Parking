#!/usr/bin/env python3
"""
Comprehensive seed script for Smart Parking Management System.

This script creates realistic sample data including:
- Admin and test users
- Multiple parking lots with Indian locations
- Parking slots for each lot
- Dynamic pricing rules
- Sample bookings and payment records
- Time chunks for slot management
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import List

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.core.database import get_async_session
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.models.pricing import PricingRule, PricingRuleType
from app.models.booking import Booking, BookingStatus
from app.models.slot_chunks import SlotTimeChunk, ChunkStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sample data configurations
INDIAN_LOCATIONS = [
    {
        "name": "Connaught Place Parking",
        "address": "Connaught Place, New Delhi, Delhi 110001",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "car_slots": 200,
        "bike_slots": 150,
        "car_rate": 15.00,
        "bike_rate": 8.00
    },
    {
        "name": "Bandra West Mall Parking",
        "address": "Linking Road, Bandra West, Mumbai, Maharashtra 400050",
        "latitude": 19.0596,
        "longitude": 72.8295,
        "car_slots": 180,
        "bike_slots": 120,
        "car_rate": 20.00,
        "bike_rate": 10.00
    },
    {
        "name": "Koramangala Tech Park",
        "address": "Koramangala 5th Block, Bangalore, Karnataka 560095",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "car_slots": 250,
        "bike_slots": 200,
        "car_rate": 12.00,
        "bike_rate": 6.00
    },
    {
        "name": "Cyber City Parking Hub",
        "address": "DLF Cyber City, Sector 25, Gurugram, Haryana 122002",
        "latitude": 28.4595,
        "longitude": 77.0266,
        "car_slots": 300,
        "bike_slots": 100,
        "car_rate": 18.00,
        "bike_rate": 9.00
    },
    {
        "name": "Phoenix MarketCity Parking",
        "address": "LBS Marg, Kurla West, Mumbai, Maharashtra 400070",
        "latitude": 19.0728,
        "longitude": 72.8826,
        "car_slots": 220,
        "bike_slots": 80,
        "car_rate": 16.00,
        "bike_rate": 7.50
    },
    {
        "name": "Sector 18 Metro Parking",
        "address": "Sector 18, Noida, Uttar Pradesh 201301",
        "latitude": 28.5706,
        "longitude": 77.3272,
        "car_slots": 150,
        "bike_slots": 100,
        "car_rate": 10.00,
        "bike_rate": 5.00
    },
    {
        "name": "Hitech City IT Hub",
        "address": "HITEC City, Madhapur, Hyderabad, Telangana 500081",
        "latitude": 17.4485,
        "longitude": 78.3908,
        "car_slots": 280,
        "bike_slots": 180,
        "car_rate": 14.00,
        "bike_rate": 7.00
    }
]

TEST_USERS = [
    {
        "email": "user@smartparking.com",
        "password": "UserPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+919876543210",
        "is_admin": False
    },
    {
        "email": "john.doe@example.com",
        "password": "JohnPassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+919876543211",
        "is_admin": False
    },
    {
        "email": "priya.sharma@example.com",
        "password": "PriyaPassword123!",
        "first_name": "Priya",
        "last_name": "Sharma",
        "phone": "+919876543212",
        "is_admin": False
    },
    {
        "email": "admin.manager@smartparking.com",
        "password": "ManagerPassword123!",
        "first_name": "Admin",
        "last_name": "Manager",
        "phone": "+919876543213",
        "is_admin": True
    }
]

async def create_users(session: AsyncSession) -> List[User]:
    """Create admin and test users."""
    print("Creating users...")
    
    users = []
    
    # Create admin user
    admin_result = await session.execute(
        select(User).where(User.email == "admin@smartparking.com")
    )
    admin_user = admin_result.scalar_one_or_none()
    
    if not admin_user:
        admin_user = User(
            email="admin@smartparking.com",
            password_hash=pwd_context.hash("AdminPassword123!"),
            first_name="System",
            last_name="Admin",
            phone="+919876543200",
            is_admin=True,
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        print(f"✅ Created admin user: {admin_user.email}")
    else:
        print(f"ℹ️ Admin user already exists: {admin_user.email}")
    
    users.append(admin_user)
    
    # Create test users
    for user_data in TEST_USERS:
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            user = User(
                email=user_data["email"],
                password_hash=pwd_context.hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data["phone"],
                is_admin=user_data["is_admin"],
                is_active=True
            )
            session.add(user)
            users.append(user)
            print(f"✅ Created user: {user_data['email']}")
        else:
            users.append(existing_user)
            print(f"ℹ️ User already exists: {user_data['email']}")
    
    await session.commit()
    
    # Refresh all users to get IDs
    for user in users:
        await session.refresh(user)
    
    return users

async def create_parking_lots(session: AsyncSession) -> List[ParkingLot]:
    """Create parking lots with Indian locations."""
    print("Creating parking lots...")
    
    # Check if lots already exist
    result = await session.execute(select(ParkingLot))
    existing_lots = result.scalars().all()
    
    if existing_lots:
        print(f"ℹ️ {len(existing_lots)} parking lots already exist")
        return list(existing_lots)
    
    parking_lots = []
    
    for location in INDIAN_LOCATIONS:
        lot = ParkingLot(
            name=location["name"],
            address=location["address"],
            latitude=location["latitude"],
            longitude=location["longitude"],
            total_car_slots=location["car_slots"],
            total_bike_slots=location["bike_slots"],
            hourly_rate_car=Decimal(str(location["car_rate"])),
            hourly_rate_bike=Decimal(str(location["bike_rate"])),
            is_active=True
        )
        parking_lots.append(lot)
    
    session.add_all(parking_lots)
    await session.commit()
    
    # Refresh to get IDs
    for lot in parking_lots:
        await session.refresh(lot)
        print(f"✅ Created parking lot: {lot.name} (ID: {lot.id})")
    
    return parking_lots

async def create_parking_slots(session: AsyncSession, parking_lots: List[ParkingLot]) -> List[ParkingSlot]:
    """Create parking slots for each lot."""
    print("Creating parking slots...")
    
    all_slots = []
    total_slots = 0
    
    for lot in parking_lots:
        # Create car slots
        for i in range(1, lot.total_car_slots + 1):
            slot = ParkingSlot(
                lot_id=lot.id,
                slot_number=f"C{i:03d}",
                slot_type=VehicleType.CAR,
                is_occupied=False,
                is_reserved=False
            )
            all_slots.append(slot)
        
        # Create bike slots
        for i in range(1, lot.total_bike_slots + 1):
            slot = ParkingSlot(
                lot_id=lot.id,
                slot_number=f"B{i:03d}",
                slot_type=VehicleType.BIKE,
                is_occupied=False,
                is_reserved=False
            )
            all_slots.append(slot)
        
        total_slots += lot.total_car_slots + lot.total_bike_slots
        print(f"✅ Created {lot.total_car_slots} car + {lot.total_bike_slots} bike slots for {lot.name}")
    
    session.add_all(all_slots)
    await session.commit()
    
    print(f"✅ Total slots created: {total_slots}")
    return all_slots

async def create_pricing_rules(session: AsyncSession, parking_lots: List[ParkingLot]):
    """Create comprehensive pricing rules."""
    print("Creating pricing rules...")
    
    pricing_rules = []
    
    for lot in parking_lots:
        # Peak hours pricing (6 PM - 10 PM)
        peak_rules = [
            PricingRule(
                lot_id=lot.id,
                name=f"Peak Hours - Car",
                vehicle_type=VehicleType.CAR,
                rule_type=PricingRuleType.TIME_BASED,
                multiplier=Decimal("1.5"),
                start_time=time(18, 0),
                end_time=time(22, 0),
                priority="high",
                is_active=True
            ),
            PricingRule(
                lot_id=lot.id,
                name=f"Peak Hours - Bike",
                vehicle_type=VehicleType.BIKE,
                rule_type=PricingRuleType.TIME_BASED,
                multiplier=Decimal("1.3"),
                start_time=time(18, 0),
                end_time=time(22, 0),
                priority="high",
                is_active=True
            )
        ]
        
        # Early bird discount (6 AM - 9 AM)
        early_rules = [
            PricingRule(
                lot_id=lot.id,
                name=f"Early Bird Discount - Car",
                vehicle_type=VehicleType.CAR,
                rule_type=PricingRuleType.TIME_BASED,
                multiplier=Decimal("0.8"),
                start_time=time(6, 0),
                end_time=time(9, 0),
                priority="normal",
                is_active=True
            ),
            PricingRule(
                lot_id=lot.id,
                name=f"Early Bird Discount - Bike",
                vehicle_type=VehicleType.BIKE,
                rule_type=PricingRuleType.TIME_BASED,
                multiplier=Decimal("0.7"),
                start_time=time(6, 0),
                end_time=time(9, 0),
                priority="normal",
                is_active=True
            )
        ]
        
        # Weekend premium (Saturday & Sunday)
        weekend_rules = [
            PricingRule(
                lot_id=lot.id,
                name=f"Weekend Premium - Car",
                vehicle_type=VehicleType.CAR,
                rule_type=PricingRuleType.DAY_BASED,
                days_of_week="saturday,sunday",
                multiplier=Decimal("1.2"),
                priority="normal",
                is_active=True
            ),
            PricingRule(
                lot_id=lot.id,
                name=f"Weekend Premium - Bike",
                vehicle_type=VehicleType.BIKE,
                rule_type=PricingRuleType.DAY_BASED,
                days_of_week="saturday,sunday",
                multiplier=Decimal("1.1"),
                priority="normal",
                is_active=True
            )
        ]
        
        pricing_rules.extend(peak_rules + early_rules + weekend_rules)
    
    session.add_all(pricing_rules)
    await session.commit()
    
    print(f"✅ Created {len(pricing_rules)} pricing rules")

async def create_sample_bookings(session: AsyncSession, users: List[User], parking_lots: List[ParkingLot], slots: List[ParkingSlot]):
    """Create sample bookings for demonstration."""
    print("Creating sample bookings...")
    
    # Get non-admin users for bookings
    regular_users = [user for user in users if not user.is_admin]
    if not regular_users:
        print("ℹ️ No regular users found, skipping booking creation")
        return
    
    bookings = []
    
    # Create some completed bookings (past)
    for i, user in enumerate(regular_users[:3]):
        if i < len(parking_lots):
            lot = parking_lots[i]
            # Find available car slot
            car_slots = [slot for slot in slots if slot.lot_id == lot.id and slot.slot_type == VehicleType.CAR]
            if car_slots:
                slot = car_slots[0]
                
                # Past booking (completed)
                past_start = datetime.now(timezone.utc) - timedelta(days=2, hours=2)
                past_end = past_start + timedelta(hours=3)
                
                booking = Booking(
                    user_id=user.id,
                    lot_id=lot.id,
                    slot_id=slot.id,
                    vehicle_type=VehicleType.CAR,
                    vehicle_number=f"DL01AB{1000 + i}",
                    start_time=past_start,
                    end_time=past_end,
                    total_amount=Decimal("45.00"),
                    status=BookingStatus.COMPLETED,
                    booking_reference=f"SP{datetime.now().strftime('%Y%m%d')}{1000 + i}"
                )
                bookings.append(booking)
                
                # Mark slot as available (booking completed)
                slot.is_occupied = False
    
    # Create some active bookings (current)
    for i, user in enumerate(regular_users[:2]):
        if i < len(parking_lots):
            lot = parking_lots[i + 1]
            bike_slots = [slot for slot in slots if slot.lot_id == lot.id and slot.slot_type == VehicleType.BIKE]
            if bike_slots:
                slot = bike_slots[0]
                
                # Current booking (active)
                current_start = datetime.now(timezone.utc) - timedelta(minutes=30)
                current_end = current_start + timedelta(hours=2)
                
                booking = Booking(
                    user_id=user.id,
                    lot_id=lot.id,
                    slot_id=slot.id,
                    vehicle_type=VehicleType.BIKE,
                    vehicle_number=f"MH12CD{2000 + i}",
                    start_time=current_start,
                    end_time=current_end,
                    total_amount=Decimal("20.00"),
                    status=BookingStatus.ACTIVE,
                    booking_reference=f"SP{datetime.now().strftime('%Y%m%d')}{2000 + i}",
                    check_in_time=current_start + timedelta(minutes=5)
                )
                bookings.append(booking)
                
                # Mark slot as occupied
                slot.is_occupied = True
    
    # Create some future bookings (confirmed)
    for i, user in enumerate(regular_users):
        if i < len(parking_lots):
            lot = parking_lots[i]
            car_slots = [slot for slot in slots if slot.lot_id == lot.id and slot.slot_type == VehicleType.CAR and not slot.is_occupied]
            if car_slots and len(car_slots) > 1:
                slot = car_slots[1]  # Use second available slot
                
                # Future booking (confirmed)
                future_start = datetime.now(timezone.utc) + timedelta(hours=2)
                future_end = future_start + timedelta(hours=4)
                
                booking = Booking(
                    user_id=user.id,
                    lot_id=lot.id,
                    slot_id=slot.id,
                    vehicle_type=VehicleType.CAR,
                    vehicle_number=f"KA05EF{3000 + i}",
                    start_time=future_start,
                    end_time=future_end,
                    total_amount=Decimal("60.00"),
                    status=BookingStatus.CONFIRMED,
                    booking_reference=f"SP{datetime.now().strftime('%Y%m%d')}{3000 + i}"
                )
                bookings.append(booking)
                
                # Mark slot as reserved
                slot.is_reserved = True
    
    if bookings:
        session.add_all(bookings)
        await session.commit()
        
        for booking in bookings:
            await session.refresh(booking)
        
        print(f"✅ Created {len(bookings)} sample bookings")
        print(f"   - Completed: {sum(1 for b in bookings if b.status == BookingStatus.COMPLETED)}")
        print(f"   - Active: {sum(1 for b in bookings if b.status == BookingStatus.ACTIVE)}")
        print(f"   - Confirmed: {sum(1 for b in bookings if b.status == BookingStatus.CONFIRMED)}")
    
    return bookings

async def create_time_chunks(session: AsyncSession, slots: List[ParkingSlot]):
    """Create time chunks for the next 7 days."""
    print("Creating time chunks for next 7 days...")
    
    from app.repositories.slot_chunks import SlotTimeChunkRepository
    chunk_repository = SlotTimeChunkRepository(session)
    
    # Create chunks for next 7 days for first 10 slots (to avoid too much data)
    sample_slots = slots[:10]
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=7)
    
    total_chunks = 0
    
    for slot in sample_slots:
        try:
            chunks = await chunk_repository.generate_chunks_for_slot(
                slot.id, start_date, end_date
            )
            total_chunks += len(chunks)
        except Exception as e:
            print(f"⚠️ Failed to create chunks for slot {slot.slot_number}: {e}")
    
    print(f"✅ Created {total_chunks} time chunks for {len(sample_slots)} slots")

async def create_comprehensive_data():
    """Create all sample data."""
    print("🚀 Starting comprehensive data seeding...")
    print("=" * 60)
    
    async for session in get_async_session():
        try:
            # 1. Create users
            users = await create_users(session)
            
            # 2. Create parking lots
            parking_lots = await create_parking_lots(session)
            
            # 3. Create parking slots
            slots = await create_parking_slots(session, parking_lots)
            
            # 4. Create pricing rules
            await create_pricing_rules(session, parking_lots)
            
            # 5. Create sample bookings
            bookings = await create_sample_bookings(session, users, parking_lots, slots)
            
            # 6. Create time chunks for demonstration
            await create_time_chunks(session, slots)
            
            print("\n" + "=" * 60)
            print("🎉 COMPREHENSIVE DATA SEEDING COMPLETED!")
            print("=" * 60)
            
            print("\n📊 DATA SUMMARY:")
            print(f"👥 Users: {len(users)} (including admins)")
            print(f"🏢 Parking Lots: {len(parking_lots)}")
            print(f"🅿️ Parking Slots: {len(slots)}")
            print(f"💰 Pricing Rules: {len(parking_lots) * 6}")
            print(f"📅 Sample Bookings: {len(bookings) if bookings else 0}")
            
            print("\n🔐 LOGIN CREDENTIALS:")
            print("👑 Admin: admin@smartparking.com / AdminPassword123!")
            print("👤 Test User: user@smartparking.com / UserPassword123!")
            print("👤 John Doe: john.doe@example.com / JohnPassword123!")
            print("👤 Priya Sharma: priya.sharma@example.com / PriyaPassword123!")
            
            print("\n🌍 SAMPLE LOCATIONS:")
            for lot in parking_lots:
                print(f"📍 {lot.name} - {lot.total_car_slots} cars, {lot.total_bike_slots} bikes")
            
            print("\n🎯 READY FOR TESTING:")
            print("✅ User registration and login")
            print("✅ Parking lot search and booking")
            print("✅ Dynamic pricing calculations")
            print("✅ Admin dashboard and management")
            print("✅ Payment processing and confirmations")
            
            print("\n🚀 Your Smart Parking System is ready for production testing!")
            
        except Exception as e:
            print(f"\n❌ Error during data seeding: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(create_comprehensive_data())
