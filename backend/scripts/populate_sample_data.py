#!/usr/bin/env python3
"""
Populate the database with sample data for testing.

This script creates:
- Admin user
- Sample parking lots
- Sample parking slots
- Sample pricing rules
"""

import asyncio
import sys
import os
from datetime import datetime, time
from decimal import Decimal

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.core.database import get_async_session
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSlot, VehicleType
from app.models.pricing import PricingRule, PricingRuleType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user(session: AsyncSession):
    """Create an admin user if it doesn't exist."""
    print("Creating admin user...")
    
    # Check if admin user already exists
    from sqlalchemy import select
    result = await session.execute(
        select(User).where(User.email == "admin@smartparking.com")
    )
    existing_admin = result.scalar_one_or_none()
    
    if existing_admin:
        print(f"ℹ️ Admin user already exists with ID: {existing_admin.id}")
        return existing_admin
    
    admin_user = User(
        email="admin@smartparking.com",
        password_hash=pwd_context.hash("AdminPassword123!"),
        first_name="Admin",
        last_name="User",
        phone="+1234567890",
        is_admin=True,
        is_active=True
    )
    
    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)
    print(f"✅ Admin user created with ID: {admin_user.id}")
    return admin_user

async def create_sample_parking_lots(session: AsyncSession):
    """Create sample parking lots if they don't exist."""
    print("Creating sample parking lots...")
    
    # Check if parking lots already exist
    from sqlalchemy import select
    result = await session.execute(select(ParkingLot))
    existing_lots = result.scalars().all()
    
    if existing_lots:
        print(f"ℹ️ {len(existing_lots)} parking lots already exist")
        return existing_lots
    
    parking_lots = [
        ParkingLot(
            name="Downtown Plaza Parking",
            address="123 Main Street, Downtown, NY 10001",
            latitude=40.7128,
            longitude=-74.0060,
            total_car_slots=150,
            total_bike_slots=75,
            hourly_rate_car=Decimal("8.00"),
            hourly_rate_bike=Decimal("3.00"),
            is_active=True
        ),
        ParkingLot(
            name="Airport Long-Term Parking",
            address="456 Airport Drive, Queens, NY 11430",
            latitude=40.6413,
            longitude=-73.7781,
            total_car_slots=300,
            total_bike_slots=50,
            hourly_rate_car=Decimal("12.00"),
            hourly_rate_bike=Decimal("4.00"),
            is_active=True
        ),
        ParkingLot(
            name="Shopping Mall Parking",
            address="789 Mall Avenue, Brooklyn, NY 11201",
            latitude=40.6892,
            longitude=-73.9442,
            total_car_slots=200,
            total_bike_slots=100,
            hourly_rate_car=Decimal("5.00"),
            hourly_rate_bike=Decimal("2.00"),
            is_active=True
        ),
        ParkingLot(
            name="University Campus Parking",
            address="321 College Street, Manhattan, NY 10003",
            latitude=40.7282,
            longitude=-73.9942,
            total_car_slots=100,
            total_bike_slots=150,
            hourly_rate_car=Decimal("6.00"),
            hourly_rate_bike=Decimal("2.50"),
            is_active=True
        )
    ]
    
    session.add_all(parking_lots)
    await session.commit()
    
    # Refresh to get IDs
    for lot in parking_lots:
        await session.refresh(lot)
        print(f"✅ Created parking lot: {lot.name} (ID: {lot.id})")
    
    return parking_lots

async def create_parking_slots(session: AsyncSession, parking_lots):
    """Create parking slots for each lot."""
    print("Creating parking slots...")
    
    total_slots = 0
    
    for lot in parking_lots:
        # Create car slots
        car_slots = []
        for i in range(1, lot.total_car_slots + 1):
            slot = ParkingSlot(
                lot_id=lot.id,
                slot_number=f"C{i:03d}",
                slot_type=VehicleType.CAR,
                is_occupied=False,
                is_reserved=False
            )
            car_slots.append(slot)
        
        # Create bike slots
        bike_slots = []
        for i in range(1, lot.total_bike_slots + 1):
            slot = ParkingSlot(
                lot_id=lot.id,
                slot_number=f"B{i:03d}",
                slot_type=VehicleType.BIKE,
                is_occupied=False,
                is_reserved=False
            )
            bike_slots.append(slot)
        
        all_slots = car_slots + bike_slots
        session.add_all(all_slots)
        total_slots += len(all_slots)
        
        print(f"✅ Created {len(car_slots)} car slots and {len(bike_slots)} bike slots for {lot.name}")
    
    await session.commit()
    print(f"✅ Total slots created: {total_slots}")

async def create_pricing_rules(session: AsyncSession, parking_lots):
    """Create sample pricing rules."""
    print("Creating pricing rules...")
    
    pricing_rules = []
    
    for lot in parking_lots:
        # Peak hours pricing (6 PM - 10 PM) - higher rates
        peak_car_rule = PricingRule(
            lot_id=lot.id,
            name=f"{lot.name} - Peak Hours Car",
            vehicle_type=VehicleType.CAR,
            rule_type=PricingRuleType.TIME_BASED,
            multiplier=Decimal("1.5"),
            start_time=time(18, 0),
            end_time=time(22, 0),
            priority=1,
            is_active=True
        )
        
        peak_bike_rule = PricingRule(
            lot_id=lot.id,
            name=f"{lot.name} - Peak Hours Bike",
            vehicle_type=VehicleType.BIKE,
            rule_type=PricingRuleType.TIME_BASED,
            multiplier=Decimal("1.3"),
            start_time=time(18, 0),
            end_time=time(22, 0),
            priority=1,
            is_active=True
        )
        
        # Early morning discount (6 AM - 9 AM) - lower rates
        early_car_rule = PricingRule(
            lot_id=lot.id,
            name=f"{lot.name} - Early Bird Car",
            vehicle_type=VehicleType.CAR,
            rule_type=PricingRuleType.TIME_BASED,
            multiplier=Decimal("0.8"),
            start_time=time(6, 0),
            end_time=time(9, 0),
            priority=2,
            is_active=True
        )
        
        early_bike_rule = PricingRule(
            lot_id=lot.id,
            name=f"{lot.name} - Early Bird Bike",
            vehicle_type=VehicleType.BIKE,
            rule_type=PricingRuleType.TIME_BASED,
            multiplier=Decimal("0.7"),
            start_time=time(6, 0),
            end_time=time(9, 0),
            priority=2,
            is_active=True
        )
        
        pricing_rules.extend([peak_car_rule, peak_bike_rule, early_car_rule, early_bike_rule])
    
    session.add_all(pricing_rules)
    await session.commit()
    
    print(f"✅ Created {len(pricing_rules)} pricing rules")

async def main():
    """Main function to populate sample data."""
    print("🚀 Starting sample data population...")
    
    async for session in get_async_session():
        try:
            # Create admin user
            admin_user = await create_admin_user(session)
            
            # Create parking lots
            parking_lots = await create_sample_parking_lots(session)
            
            # Create parking slots
            await create_parking_slots(session, parking_lots)
            
            # Create pricing rules
            await create_pricing_rules(session, parking_lots)
            
            print("\n🎉 Sample data population completed successfully!")
            print("\n📋 Summary:")
            print(f"- Admin user: admin@smartparking.com / AdminPassword123!")
            print(f"- Parking lots: {len(parking_lots)}")
            print(f"- Total car slots: {sum(lot.total_car_slots for lot in parking_lots)}")
            print(f"- Total bike slots: {sum(lot.total_bike_slots for lot in parking_lots)}")
            print(f"- Pricing rules: {len(parking_lots) * 4}")
            
            print("\n🔧 You can now test the APIs with:")
            print("- Register/Login users")
            print("- Search parking lots")
            print("- Check availability")
            print("- Create bookings")
            print("- Admin operations")
            
        except Exception as e:
            print(f"❌ Error populating sample data: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(main())
