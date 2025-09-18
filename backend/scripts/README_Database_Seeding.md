# 🗄️ Database Seeding & Sample Data Guide

This directory contains scripts and tools for managing sample data in the Smart Parking Management System.

## 📋 Available Scripts

### 🌱 **Comprehensive Seed Script**
```bash
python seed_comprehensive_data.py
```
**Features:**
- Creates admin and test users with Indian phone numbers
- Adds 7 parking lots with realistic Indian locations
- Generates parking slots for each lot
- Creates dynamic pricing rules (peak hours, early bird, weekend)
- Adds sample bookings (completed, active, confirmed)
- Creates time chunks for slot management

### 🗄️ **Database Dump Manager**
```bash
python create_db_dump.py <command>
```
**Commands:**
- `seed` - Run comprehensive seeding
- `dump` - Create PostgreSQL dump file
- `export` - Create JSON export
- `stats` - Show database statistics
- `restore <file>` - Restore from dump

### 📄 **Quick SQL Seed**
```bash
psql -U postgres -d smart_parking -f seed_data.sql
```
**Features:**
- Essential users and parking lots
- Basic pricing rules
- Quick setup for testing

### 🛠️ **Interactive Shell Script**
```bash
./seed_database.sh
```
**Menu Options:**
1. Comprehensive Python seeding
2. Quick SQL seeding
3. Create database dump
4. Show statistics
5. Run migrations
6. Reset database

## 📊 Sample Data Overview

### 👥 **Users Created:**
| Email | Password | Role | Phone |
|-------|----------|------|-------|
| admin@smartparking.com | AdminPassword123! | Admin | +919876543200 |
| user@smartparking.com | UserPassword123! | User | +919876543210 |
| john.doe@example.com | JohnPassword123! | User | +919876543211 |
| priya.sharma@example.com | PriyaPassword123! | User | +919876543212 |
| admin.manager@smartparking.com | ManagerPassword123! | Admin | +919876543213 |

### 🏢 **Parking Locations (Indian Cities):**
1. **Connaught Place Parking** - New Delhi (200 car, 150 bike slots)
2. **Bandra West Mall Parking** - Mumbai (180 car, 120 bike slots)
3. **Koramangala Tech Park** - Bangalore (250 car, 200 bike slots)
4. **Cyber City Parking Hub** - Gurugram (300 car, 100 bike slots)
5. **Phoenix MarketCity Parking** - Mumbai (220 car, 80 bike slots)
6. **Sector 18 Metro Parking** - Noida (150 car, 100 bike slots)
7. **Hitech City IT Hub** - Hyderabad (280 car, 180 bike slots)

### 💰 **Pricing Rules:**
- **Peak Hours** (6 PM - 10 PM): 1.5x multiplier for cars, 1.3x for bikes
- **Early Bird** (6 AM - 9 AM): 0.8x multiplier for cars, 0.7x for bikes
- **Weekend Premium** (Sat-Sun): 1.2x multiplier for cars, 1.1x for bikes

### 📅 **Sample Bookings:**
- **Completed bookings** (past dates)
- **Active bookings** (currently in progress)
- **Confirmed bookings** (future reservations)

## 🚀 Quick Setup Commands

### **Fresh Installation:**
```bash
# 1. Start services
docker-compose up -d

# 2. Run migrations
docker-compose exec api alembic upgrade head

# 3. Seed comprehensive data
docker-compose exec api python scripts/seed_comprehensive_data.py

# 4. Verify data
docker-compose exec api python scripts/create_db_dump.py stats
```

### **Reset and Reseed:**
```bash
# 1. Interactive reset (DANGER!)
./scripts/seed_database.sh

# 2. Choose option 6 (Reset Database)
# 3. Choose option 1 (Comprehensive Seeding)
```

### **Create Backup:**
```bash
# Create timestamped dump
python scripts/create_db_dump.py dump

# Or use shell script
./scripts/seed_database.sh
# Choose option 3 (Create Database Dump)
```

## 📁 Database Dumps

### **Available Dump:**
- **smart_parking_with_sample_data_20250918_134126.sql**
  - Complete database with all sample data
  - 23 users, 7 parking lots, 1339 slots, 64 bookings
  - Ready for production testing

### **Restore from Dump:**
```bash
# Method 1: Using dump manager
python create_db_dump.py restore smart_parking_with_sample_data_20250918_134126.sql

# Method 2: Direct psql
docker-compose exec -T db psql -U postgres < database_dumps/smart_parking_with_sample_data_20250918_134126.sql
```

## 🎯 Testing Scenarios

### **User Testing:**
- Login with any test user credentials
- Search for parking lots by location
- Create bookings with different vehicle types
- Test payment flow with various methods

### **Admin Testing:**
- Login with admin credentials
- Access admin dashboard
- Manage parking lots and pricing rules
- View analytics and reports
- Manage user accounts

### **API Testing:**
- All 42 endpoints populated with realistic data
- Pricing calculations with dynamic rules
- Booking workflow with time chunks
- Authentication and authorization

## 🔐 Security Notes

### **Default Passwords:**
All default passwords use **bcrypt hashing** and should be changed in production:
- Admin: `AdminPassword123!`
- Users: `UserPassword123!`, `JohnPassword123!`, etc.

### **Test Data:**
- All phone numbers use Indian format (+91)
- Email addresses are test/example domains
- Vehicle numbers follow Indian format
- Locations are real Indian cities

## 🎉 Ready for Production Testing!

Your Smart Parking Management System now has:
- ✅ **Complete sample data** for all features
- ✅ **Realistic Indian locations** and data
- ✅ **Multiple user roles** for testing
- ✅ **Dynamic pricing scenarios** 
- ✅ **Booking history** for demonstration
- ✅ **Database backup** for easy restoration

**Start testing your application with realistic, comprehensive data!** 🚀
