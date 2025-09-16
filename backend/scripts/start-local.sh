#!/bin/bash

# Smart Parking Management System - Local Development Startup Script

echo "🚀 Starting Smart Parking Management System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   On macOS: Open Docker Desktop application"
    echo "   On Linux: sudo systemctl start docker"
    echo "   On Windows: Start Docker Desktop"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker is running"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/smart_parking
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/smart_parking

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
DEBUG=true

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:4200", "http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Booking Configuration
MAX_BOOKING_DURATION_HOURS=24
BOOKING_EXPIRY_MINUTES=10
EOF
    echo "✅ Created .env file"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove old images to avoid cache issues
echo "🧹 Cleaning up old images..."
docker-compose build --no-cache

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "❌ API is not responding"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not responding"
fi

# Check PostgreSQL
if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is not responding"
fi

# Check Celery
if docker-compose logs celery_worker | grep -q "ready"; then
    echo "✅ Celery worker is running"
else
    echo "❌ Celery worker is not ready"
fi

echo ""
echo "🎉 Smart Parking Management System is starting up!"
echo ""
echo "📋 Available services:"
echo "   🌐 API Server:     http://localhost:8000"
echo "   📖 API Docs:       http://localhost:8000/docs"
echo "   🗄️  Database:      localhost:5432 (postgres/password)"
echo "   💾 Redis:          localhost:6379"
echo "   🌸 Flower:         http://localhost:5555"
echo ""
echo "📋 Useful commands:"
echo "   📊 View logs:      docker-compose logs -f"
echo "   🛑 Stop services:  docker-compose down"
echo "   🔧 Rebuild:        docker-compose build --no-cache"
echo "   🧪 Run tests:      docker-compose exec api pytest"
echo ""
echo "🚀 Ready for development!"
