#!/usr/bin/env python3
"""
Database dump and restore script for Smart Parking Management System.

This script can:
1. Create a database dump with sample data
2. Restore database from dump
3. Create SQL seed files
"""

import asyncio
import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.core.database import get_async_session
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSlot
from app.models.pricing import PricingRule
from app.models.booking import Booking

class DatabaseManager:
    """Database dump and restore manager."""
    
    def __init__(self):
        self.dump_dir = Path("database_dumps")
        self.dump_dir.mkdir(exist_ok=True)
        
        # Database connection info (from Docker Compose)
        self.db_config = {
            "host": "localhost",
            "port": "5432",
            "database": "smart_parking",
            "username": "postgres",
            "password": "password"
        }
    
    async def create_sql_dump(self, filename: str = None):
        """Create a PostgreSQL dump file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"smart_parking_dump_{timestamp}.sql"
        
        dump_path = self.dump_dir / filename
        
        print(f"🗄️ Creating PostgreSQL dump: {dump_path}")
        
        # Use pg_dump to create SQL dump
        cmd = [
            "pg_dump",
            f"--host={self.db_config['host']}",
            f"--port={self.db_config['port']}",
            f"--username={self.db_config['username']}",
            f"--dbname={self.db_config['database']}",
            "--no-password",
            "--verbose",
            "--clean",
            "--if-exists",
            "--create",
            "--inserts",
            f"--file={dump_path}"
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_config["password"]
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ SQL dump created successfully: {dump_path}")
                print(f"📏 File size: {dump_path.stat().st_size / 1024:.1f} KB")
                return str(dump_path)
            else:
                print(f"❌ pg_dump failed: {result.stderr}")
                return None
        except FileNotFoundError:
            print("❌ pg_dump not found. Install PostgreSQL client tools.")
            return None
    
    async def restore_from_dump(self, dump_file: str):
        """Restore database from SQL dump."""
        dump_path = Path(dump_file)
        if not dump_path.exists():
            print(f"❌ Dump file not found: {dump_path}")
            return False
        
        print(f"📥 Restoring database from: {dump_path}")
        
        cmd = [
            "psql",
            f"--host={self.db_config['host']}",
            f"--port={self.db_config['port']}",
            f"--username={self.db_config['username']}",
            f"--dbname=postgres",  # Connect to postgres db first
            "--no-password",
            "--file", str(dump_path)
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_config["password"]
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Database restored successfully")
                return True
            else:
                print(f"❌ Restore failed: {result.stderr}")
                return False
        except FileNotFoundError:
            print("❌ psql not found. Install PostgreSQL client tools.")
            return False
    
    async def create_json_export(self, filename: str = None):
        """Create a JSON export of all data."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"smart_parking_data_{timestamp}.json"
        
        export_path = self.dump_dir / filename
        
        print(f"📄 Creating JSON export: {export_path}")
        
        async for session in get_async_session():
            try:
                export_data = {
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0.0",
                        "description": "Smart Parking Management System sample data"
                    },
                    "users": [],
                    "parking_lots": [],
                    "parking_slots": [],
                    "pricing_rules": [],
                    "bookings": []
                }
                
                # Export users
                users = await session.execute(select(User))
                for user in users.scalars().all():
                    export_data["users"].append({
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "phone": user.phone,
                        "is_admin": user.is_admin,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat()
                    })
                
                # Export parking lots
                lots = await session.execute(select(ParkingLot))
                for lot in lots.scalars().all():
                    export_data["parking_lots"].append({
                        "id": str(lot.id),
                        "name": lot.name,
                        "address": lot.address,
                        "latitude": float(lot.latitude),
                        "longitude": float(lot.longitude),
                        "total_car_slots": lot.total_car_slots,
                        "total_bike_slots": lot.total_bike_slots,
                        "hourly_rate_car": float(lot.hourly_rate_car),
                        "hourly_rate_bike": float(lot.hourly_rate_bike),
                        "is_active": lot.is_active,
                        "created_at": lot.created_at.isoformat()
                    })
                
                # Export parking slots
                slots = await session.execute(select(ParkingSlot))
                for slot in slots.scalars().all():
                    export_data["parking_slots"].append({
                        "id": str(slot.id),
                        "lot_id": str(slot.lot_id),
                        "slot_number": slot.slot_number,
                        "slot_type": slot.slot_type,
                        "is_occupied": slot.is_occupied,
                        "is_reserved": slot.is_reserved,
                        "created_at": slot.created_at.isoformat()
                    })
                
                # Export pricing rules
                rules = await session.execute(select(PricingRule))
                for rule in rules.scalars().all():
                    export_data["pricing_rules"].append({
                        "id": str(rule.id),
                        "lot_id": str(rule.lot_id),
                        "name": rule.name,
                        "vehicle_type": rule.vehicle_type,
                        "rule_type": rule.rule_type,
                        "start_time": rule.start_time.isoformat() if rule.start_time else None,
                        "end_time": rule.end_time.isoformat() if rule.end_time else None,
                        "days_of_week": rule.days_of_week,
                        "price_per_hour": float(rule.price_per_hour) if rule.price_per_hour else None,
                        "multiplier": float(rule.multiplier) if rule.multiplier else None,
                        "priority": rule.priority,
                        "is_active": rule.is_active,
                        "created_at": rule.created_at.isoformat()
                    })
                
                # Export bookings
                bookings = await session.execute(select(Booking))
                for booking in bookings.scalars().all():
                    export_data["bookings"].append({
                        "id": str(booking.id),
                        "user_id": str(booking.user_id),
                        "lot_id": str(booking.lot_id),
                        "slot_id": str(booking.slot_id) if booking.slot_id else None,
                        "vehicle_type": booking.vehicle_type,
                        "vehicle_number": booking.vehicle_number,
                        "start_time": booking.start_time.isoformat(),
                        "end_time": booking.end_time.isoformat(),
                        "total_amount": float(booking.total_amount),
                        "status": booking.status,
                        "booking_reference": booking.booking_reference,
                        "check_in_time": booking.check_in_time.isoformat() if booking.check_in_time else None,
                        "check_out_time": booking.check_out_time.isoformat() if booking.check_out_time else None,
                        "created_at": booking.created_at.isoformat()
                    })
                
                # Write JSON file
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                print(f"✅ JSON export created: {export_path}")
                print(f"📊 Data summary:")
                print(f"   - Users: {len(export_data['users'])}")
                print(f"   - Parking Lots: {len(export_data['parking_lots'])}")
                print(f"   - Parking Slots: {len(export_data['parking_slots'])}")
                print(f"   - Pricing Rules: {len(export_data['pricing_rules'])}")
                print(f"   - Bookings: {len(export_data['bookings'])}")
                
                return str(export_path)
                
            except Exception as e:
                print(f"❌ Error creating JSON export: {e}")
                return None
            finally:
                await session.close()
                break
    
    async def get_database_stats(self):
        """Get current database statistics."""
        print("📊 Current Database Statistics:")
        print("-" * 40)
        
        async for session in get_async_session():
            try:
                # Count records in each table
                tables = [
                    ("Users", User),
                    ("Parking Lots", ParkingLot),
                    ("Parking Slots", ParkingSlot),
                    ("Pricing Rules", PricingRule),
                    ("Bookings", Booking)
                ]
                
                for table_name, model in tables:
                    result = await session.execute(select(model))
                    count = len(result.scalars().all())
                    print(f"{table_name:15}: {count:4d} records")
                
            except Exception as e:
                print(f"❌ Error getting stats: {e}")
            finally:
                await session.close()
                break

async def main():
    """Main function with menu options."""
    print("🗄️ Smart Parking Database Management")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "seed":
            print("🌱 Running comprehensive data seeding...")
            await create_comprehensive_data()
            
        elif command == "dump":
            print("🗄️ Creating database dump...")
            await db_manager.create_sql_dump()
            
        elif command == "export":
            print("📄 Creating JSON export...")
            await db_manager.create_json_export()
            
        elif command == "stats":
            print("📊 Getting database statistics...")
            await db_manager.get_database_stats()
            
        elif command == "restore":
            if len(sys.argv) > 2:
                dump_file = sys.argv[2]
                print(f"📥 Restoring from dump: {dump_file}")
                await db_manager.restore_from_dump(dump_file)
            else:
                print("❌ Please provide dump file path: python create_db_dump.py restore <dump_file>")
                
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
    else:
        print_usage()

def print_usage():
    """Print usage instructions."""
    print("\n📋 Usage:")
    print("python create_db_dump.py <command>")
    print("\n🔧 Available commands:")
    print("  seed     - Create comprehensive sample data")
    print("  dump     - Create PostgreSQL dump file")
    print("  export   - Create JSON export of all data")
    print("  stats    - Show current database statistics")
    print("  restore  - Restore from dump file")
    print("\n💡 Examples:")
    print("  python create_db_dump.py seed")
    print("  python create_db_dump.py dump")
    print("  python create_db_dump.py export")
    print("  python create_db_dump.py stats")
    print("  python create_db_dump.py restore smart_parking_dump_20250918_123000.sql")

if __name__ == "__main__":
    asyncio.run(main())
