# 🐳 Docker Setup - One-Click Smart Parking System

This document explains how to run the complete Smart Parking Management System with a single command using Docker.

## 🚀 Quick Start

### **Production-Ready Setup (Full Stack)**
```bash
./start-smart-parking.sh
```
**What it does:**
- ✅ Starts all services (Backend, Frontend, Database, Redis, Celery)
- ✅ Automatically seeds comprehensive sample data
- ✅ Builds optimized Angular frontend
- ✅ Ready for production testing

### **Development Setup (Hot Reload)**
```bash
./start-dev.sh
```
**What it does:**
- ✅ Starts backend services with Docker
- ✅ Starts frontend with `ng serve` (hot reload)
- ✅ Enables development features and debugging
- ✅ Faster iteration for development

---

## 📋 Available Commands

### **Production Commands:**
```bash
./start-smart-parking.sh          # Start complete system
./start-smart-parking.sh stop     # Stop all services
./start-smart-parking.sh logs     # View service logs
./start-smart-parking.sh status   # Show service status
./start-smart-parking.sh clean    # Remove all containers and data
./start-smart-parking.sh help     # Show help
```

### **Development Commands:**
```bash
./start-dev.sh                    # Start dev environment
./start-dev.sh backend-only       # Start only backend services
./start-dev.sh stop               # Stop all services
./start-dev.sh logs               # View backend logs
./start-dev.sh help               # Show help
```

---

## 🏗️ Architecture Overview

### **Production Stack (`docker-compose.fullstack.yml`):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Angular)     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 4200    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Redis Cache   │              │
         │              │   Port: 6379    │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│ Celery Workers  │──────────────┘
                        │ + Beat + Flower │
                        │   Port: 5555    │
                        └─────────────────┘
```

### **Services Included:**
| Service | Container Name | Port | Description |
|---------|----------------|------|-------------|
| **Frontend** | `smart_parking_frontend` | 4200 | Angular app with Nginx |
| **Backend API** | `smart_parking_api` | 8000 | FastAPI with auto-reload |
| **Database** | `smart_parking_db` | 5432 | PostgreSQL with data persistence |
| **Redis** | `smart_parking_redis` | 6379 | Caching and message broker |
| **Celery Worker** | `smart_parking_worker` | - | Background task processing |
| **Celery Beat** | `smart_parking_scheduler` | - | Periodic task scheduler |
| **Celery Flower** | `smart_parking_monitor` | 5555 | Task monitoring dashboard |
| **DB Init** | `smart_parking_init` | - | One-time database seeding |

---

## 🗄️ Database Seeding

### **Automatic Seeding:**
The system automatically seeds comprehensive sample data on first startup:

- **👥 Users**: 23 users including admins and test accounts
- **🏢 Parking Lots**: 7 locations in major Indian cities
- **🅿️ Parking Slots**: 1000+ slots across all locations
- **💰 Pricing Rules**: Dynamic time-based pricing
- **📅 Bookings**: Sample booking history and active reservations

### **Manual Seeding:**
```bash
# Seed additional data
docker-compose -f docker-compose.fullstack.yml exec api python scripts/seed_comprehensive_data.py

# Check database statistics
docker-compose -f docker-compose.fullstack.yml exec api python scripts/create_db_dump.py stats
```

---

## 🌐 Access Points

### **After Starting the System:**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:4200 | See login credentials below |
| **Backend API** | http://localhost:8000 | API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive documentation |
| **Celery Monitor** | http://localhost:5555 | Task monitoring |

### **🔐 Login Credentials:**

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@smartparking.com | AdminPassword123! |
| **User** | user@smartparking.com | UserPassword123! |
| **Test User 1** | john.doe@example.com | JohnPassword123! |
| **Test User 2** | priya.sharma@example.com | PriyaPassword123! |
| **Admin Manager** | admin.manager@smartparking.com | ManagerPassword123! |

---

## 🛠️ Development Workflow

### **Full Development Setup:**
```bash
# Start everything with hot reload
./start-dev.sh

# Frontend: http://localhost:4200 (ng serve with hot reload)
# Backend: http://localhost:8000 (uvicorn with auto-reload)
```

### **Backend-Only Development:**
```bash
# Start only backend services
./start-dev.sh backend-only

# Then start frontend separately
cd frontend
ng serve
```

### **Debugging:**
```bash
# View all service logs
./start-smart-parking.sh logs

# View specific service logs
docker-compose -f docker-compose.fullstack.yml logs -f api
docker-compose -f docker-compose.fullstack.yml logs -f frontend

# Access database directly
docker-compose -f docker-compose.fullstack.yml exec db psql -U postgres -d smart_parking
```

---

## 📁 File Structure

```
/Users/manojdeka/Documents/Interviews/FuelCycle/
├── 🚀 start-smart-parking.sh          # Production startup script
├── 🛠️ start-dev.sh                    # Development startup script
├── 📋 docker-compose.fullstack.yml    # Production Docker Compose
├── 🔧 docker-compose.dev.yml          # Development Docker Compose
├── backend/
│   ├── 🐳 Dockerfile                   # Backend container definition
│   ├── 📋 docker-compose.yml          # Original backend-only compose
│   └── scripts/
│       ├── 🌱 seed_comprehensive_data.py
│       ├── 🗄️ create_db_dump.py
│       └── 📄 seed_data.sql
├── frontend/
│   ├── 🐳 Dockerfile                   # Frontend container definition
│   ├── ⚙️ nginx.conf                   # Nginx configuration
│   └── src/...                        # Angular source code
└── 📚 DOCKER_SETUP.md                 # This documentation
```

---

## 🔧 Configuration

### **Environment Variables:**
All services use development-friendly defaults:

```env
# Database
POSTGRES_DB=smart_parking
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Backend
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/smart_parking
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=true

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### **Data Persistence:**
- **Database**: `postgres_data` volume
- **Redis**: `redis_data` volume
- **Data survives**: Container restarts and rebuilds
- **Reset data**: Use `./start-smart-parking.sh clean`

---

## 🎯 Testing Scenarios

### **Frontend Testing:**
1. **User Registration & Login**
   - Register new users
   - Login with test credentials
   - Test role-based navigation

2. **Parking Operations**
   - Search parking lots by location
   - View real-time availability
   - Create bookings with different vehicle types

3. **Payment Processing**
   - Test different payment methods
   - Confirm booking workflow
   - View booking history

4. **Admin Features**
   - Access admin dashboard
   - Manage parking lots and pricing
   - View analytics and reports

### **API Testing:**
- **Documentation**: http://localhost:8000/docs
- **All 42 endpoints** populated with realistic data
- **Authentication**: JWT token-based
- **Real-time features**: WebSocket connections

---

## 🚨 Troubleshooting

### **Common Issues:**

**1. Port Already in Use:**
```bash
# Stop conflicting services
./start-smart-parking.sh stop
# Or kill specific processes
sudo lsof -ti:4200 | xargs kill -9
sudo lsof -ti:8000 | xargs kill -9
```

**2. Docker Build Fails:**
```bash
# Clean Docker cache
docker system prune -a
# Restart with fresh build
./start-smart-parking.sh
```

**3. Database Connection Issues:**
```bash
# Check database logs
docker-compose -f docker-compose.fullstack.yml logs db
# Reset database
./start-smart-parking.sh clean
```

**4. Frontend Build Fails:**
```bash
# Use development mode instead
./start-dev.sh
# Or rebuild frontend dependencies
cd frontend && npm install
```

### **Health Checks:**
```bash
# Check all service status
./start-smart-parking.sh status

# Test individual services
curl http://localhost:8000/health    # Backend health
curl http://localhost:4200          # Frontend
curl http://localhost:5555          # Celery monitor
```

---

## 🎉 Success Indicators

### **✅ System is Ready When:**
- All services show as "healthy" in `docker ps`
- Frontend loads at http://localhost:4200
- Backend API docs accessible at http://localhost:8000/docs
- Login works with test credentials
- Sample data is visible (parking lots, bookings)
- Celery tasks are processing (visible in Flower)

### **📊 Expected Sample Data:**
- **Users**: 23 (including 5 test accounts)
- **Parking Lots**: 7 (major Indian cities)
- **Parking Slots**: 1000+ (cars and bikes)
- **Bookings**: 60+ (past, current, future)
- **Pricing Rules**: Dynamic time-based rules

---

## 🚀 Ready for Production Testing!

Your Smart Parking Management System is now:
- ✅ **Fully containerized** and portable
- ✅ **One-command startup** with comprehensive data
- ✅ **Development-ready** with hot reload
- ✅ **Production-ready** with optimized builds
- ✅ **Monitoring-enabled** with Celery Flower
- ✅ **Database-persistent** across restarts

**Start testing your complete Smart Parking system now!** 🎯
