# Smart Parking Management System - Backend

A comprehensive, scalable backend system for managing smart parking lots with real-time availability, dynamic pricing, and multi-vehicle support.

## 🚀 Features

- **Multi-vehicle Support**: Cars, bikes with intelligent slot allocation (2 bikes per car slot)
- **Dynamic Pricing**: Time-based, demand-based pricing rules
- **Real-time Availability**: Live slot status with caching
- **JWT Authentication**: Secure user authentication and authorization
- **Admin Dashboard**: Complete administrative control
- **Background Tasks**: Automated booking expiry and cleanup
- **Comprehensive Testing**: Unit tests, integration tests with high coverage
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Async/Await**: High-performance async operations
- **SOLID Principles**: Clean, maintainable architecture

## 🏗️ Architecture

### Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with async SQLAlchemy
- **Caching**: Redis for performance optimization
- **Authentication**: JWT tokens with bcrypt password hashing
- **Task Queue**: Celery for background processing
- **Testing**: Pytest with async support
- **Code Quality**: Black, isort, flake8, mypy

### Project Structure

```
backend/
├── app/
│   ├── api/                  # API endpoints
│   │   └── v1/
│   │       ├── endpoints/    # Route handlers
│   │       └── api.py       # Router configuration
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   ├── database.py      # Database configuration
│   │   └── exceptions.py    # Custom exceptions
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── parking.py
│   │   ├── booking.py
│   │   └── pricing.py
│   ├── repositories/        # Data access layer
│   ├── services/           # Business logic layer
│   ├── schemas/            # Pydantic schemas
│   └── main.py            # Application entry point
├── tests/                 # Test suite
├── requirements.txt       # Dependencies
└── README.md
```

## 🔧 Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Poetry (recommended) or pip

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Update `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/smart_parking
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/smart_parking

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 3. Database Setup

```bash
# Create database
createdb smart_parking

# Run migrations (if using Alembic)
alembic upgrade head

# Or create tables directly
python -c "
import asyncio
from app.core.database import create_tables
asyncio.run(create_tables())
"
```

### 4. Start Services

```bash
# Start Redis (if not running)
redis-server

# Start Celery worker (in separate terminal)
celery -A app.tasks.celery worker --loglevel=info

# Start FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Verify Installation

Visit: `http://localhost:8000/docs` for API documentation

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_booking_service.py

# Run with verbose output
pytest -v
```

### Test Coverage

The test suite includes:

- **Unit Tests**: All services, repositories, and utilities
- **Integration Tests**: API endpoints with database
- **Edge Cases**: Boundary conditions and error scenarios
- **Performance Tests**: Load testing for critical paths

Target coverage: **>90%**

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/login        # User login
POST /api/v1/auth/refresh      # Refresh token
POST /api/v1/auth/logout       # User logout
```

### Parking Endpoints

```
GET  /api/v1/parking/lots              # List parking lots
GET  /api/v1/parking/lots/{id}         # Get lot details
GET  /api/v1/parking/lots/{id}/availability  # Real-time availability
POST /api/v1/parking/search            # Search lots by location
```

### Booking Endpoints

```
POST /api/v1/bookings                  # Create booking
GET  /api/v1/bookings/user/{user_id}   # User bookings
GET  /api/v1/bookings/{id}             # Booking details
PUT  /api/v1/bookings/{id}/cancel      # Cancel booking
POST /api/v1/bookings/{id}/checkin     # Check in
POST /api/v1/bookings/{id}/checkout    # Check out
```

### Admin Endpoints

```
POST /api/v1/admin/lots                # Create parking lot
PUT  /api/v1/admin/lots/{id}           # Update lot
DELETE /api/v1/admin/lots/{id}         # Delete lot
GET  /api/v1/admin/reports/revenue     # Revenue reports
GET  /api/v1/admin/reports/occupancy   # Occupancy reports
```

## 🔐 Security Features

- **JWT Authentication**: Stateless authentication with refresh tokens
- **Password Security**: bcrypt hashing with salt
- **CORS Protection**: Configurable origin restrictions
- **Rate Limiting**: API endpoint protection
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Response sanitization

## ⚡ Performance Optimizations

- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connections
- **Redis Caching**: Fast data retrieval
- **Query Optimization**: Indexed database queries
- **Pagination**: Large dataset handling
- **Background Tasks**: Asynchronous processing

## 🏢 Business Logic

### Slot Allocation Algorithm

```python
def allocate_slot(vehicle_type, lot_id, start_time, end_time):
    """
    Intelligent slot allocation:
    1. Cars get dedicated car slots
    2. Bikes prefer bike slots, fall back to car slots
    3. Car slots can accommodate 2 bikes simultaneously
    4. Conflict detection prevents overbooking
    """
```

### Dynamic Pricing Engine

```python
def calculate_price(lot_id, vehicle_type, start_time, end_time):
    """
    Multi-rule pricing system:
    1. Base hourly rates by vehicle type
    2. Peak hour multipliers (configurable)
    3. Weekend premiums
    4. Seasonal adjustments
    5. Demand-based surge pricing
    """
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Async PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |
| `MAX_BOOKING_DURATION_HOURS` | Max booking time | 24 |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | 100 |

### Logging Configuration

Structured logging with context:

```python
logger.info(
    "Booking created",
    user_id=user.id,
    lot_id=lot.id,
    vehicle_type=vehicle_type,
    amount=total_amount
)
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Database**: Use managed PostgreSQL (RDS, Cloud SQL)
2. **Caching**: Redis cluster for high availability
3. **Load Balancing**: Multiple FastAPI instances
4. **Monitoring**: Prometheus metrics, Grafana dashboards
5. **Logging**: Centralized logging (ELK stack)
6. **Security**: HTTPS, WAF, rate limiting

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- **Type Hints**: All functions must have type annotations
- **Docstrings**: All public methods need documentation
- **Testing**: New features require tests (>90% coverage)
- **Linting**: Code must pass black, isort, flake8, mypy

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- **Issues**: Create GitHub issue
- **Documentation**: Check `/docs` endpoint
- **Email**: support@smartparking.com

---

**Built with ❤️ for efficient urban parking management**
