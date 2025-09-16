# Smart Parking Management System - Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Docker Issues

#### ❌ "Docker daemon not running"
**Problem:** `Cannot connect to the Docker daemon at unix:///Users/manojdeka/.docker/run/docker.sock`

**Solutions:**
1. **Start Docker Desktop:**
   ```bash
   # macOS: Open Docker Desktop application
   open -a Docker
   
   # Or start from command line (if installed via Homebrew)
   brew services start docker
   ```

2. **Check Docker status:**
   ```bash
   docker info
   docker version
   ```

3. **Reset Docker if needed:**
   - Docker Desktop → Preferences → Reset → "Reset to factory defaults"

#### ❌ "Version attribute obsolete"
**Problem:** Warning about `version: '3.8'` in docker-compose.yml

**Solution:** ✅ **FIXED** - Removed version field from docker-compose.yml

### 2. Application Startup Issues

#### ❌ Import Errors
**Problem:** Module import failures

**Solutions:**
1. **Check Python environment:**
   ```bash
   python --version  # Should be 3.11+
   pip list | grep fastapi
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set PYTHONPATH:**
   ```bash
   export PYTHONPATH=/Users/manojdeka/Documents/Interviews/FuelCycle/backend:$PYTHONPATH
   ```

#### ❌ Database Connection Issues
**Problem:** Cannot connect to PostgreSQL

**Solutions:**
1. **Check if PostgreSQL is running:**
   ```bash
   docker-compose logs db
   ```

2. **Reset database:**
   ```bash
   docker-compose down
   docker volume rm backend_postgres_data
   docker-compose up -d db
   ```

### 3. Quick Start Solutions

#### Option 1: Docker Compose (Recommended)
```bash
# Ensure Docker is running
docker info

# Start all services
cd /Users/manojdeka/Documents/Interviews/FuelCycle/backend
docker-compose up --build

# Check service health
curl http://localhost:8000/health
```

#### Option 2: Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis locally
brew install postgresql redis
brew services start postgresql
brew services start redis

# Create database
createdb smart_parking

# Run the application
python setup.py  # Setup environment
uvicorn app.main:app --reload
```

#### Option 3: Minimal Setup (Testing)
```bash
# Use SQLite for testing
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/0"

# Run without Docker
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Environment Configuration

#### Create .env file:
```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/smart_parking
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/smart_parking
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=true
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
EOF
```

### 5. Testing the Setup

#### Health Check:
```bash
# Check API
curl http://localhost:8000/health

# Check documentation
open http://localhost:8000/docs

# Test endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Run Tests:
```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Specific test
pytest tests/test_services/test_booking_service.py -v
```

### 6. Service Status Check

#### Check All Services:
```bash
# Docker services
docker-compose ps

# Application logs
docker-compose logs -f api

# Database
docker-compose exec db psql -U postgres -d smart_parking -c "SELECT 1;"

# Redis
docker-compose exec redis redis-cli ping

# Celery
docker-compose logs celery_worker
```

### 7. Development Workflow

#### Recommended Development Setup:
```bash
# 1. Start infrastructure
docker-compose up -d db redis

# 2. Run API locally for faster development
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/smart_parking"
uvicorn app.main:app --reload

# 3. Run tests
pytest --cov=app

# 4. Code formatting
black app/
isort app/
flake8 app/
```

### 8. Debugging Tips

#### Enable Debug Logging:
```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Database Debug:
```python
# In app/core/database.py
async_engine = create_async_engine(
    settings.database_url,
    echo=True,  # Shows SQL queries
    # ... other settings
)
```

#### Check Dependencies:
```bash
# Verify all imports work
python -c "
import app.main
import app.models
import app.services
import app.repositories
print('✅ All imports successful')
"
```

### 9. Production Deployment

#### Environment Variables:
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-secret-key>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
```

#### Docker Production:
```bash
# Build for production
docker build -t smart-parking-api .

# Run with production settings
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=<prod-db> \
  smart-parking-api
```

## 🆘 Getting Help

If you're still having issues:

1. **Check logs:** `docker-compose logs -f`
2. **Verify ports:** `lsof -i :8000,5432,6379`
3. **Reset everything:** `docker-compose down && docker system prune -f`
4. **Check system resources:** Ensure sufficient disk space and memory

## ✅ Success Indicators

When everything is working correctly, you should see:

- ✅ API responds at http://localhost:8000/health
- ✅ Documentation at http://localhost:8000/docs
- ✅ Database accepts connections
- ✅ Redis responds to ping
- ✅ Celery worker shows "ready"
- ✅ All tests pass with `pytest`

---

**💡 Pro Tip:** Use the `python setup.py` script for automated environment setup!
