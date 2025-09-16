"""Setup script for Smart Parking Management System."""

import os
import sys
import subprocess
from pathlib import Path


def check_docker():
    """Check if Docker is running."""
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_env_file():
    """Create .env file if it doesn't exist."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    env_content = """# Database Configuration
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
"""
    
    with open(env_path, "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file")


def setup_local_development():
    """Setup local development environment."""
    print("🚀 Setting up Smart Parking Management System...")
    
    # Check Docker
    if not check_docker():
        print("❌ Docker is not running or not installed.")
        print("Please install and start Docker Desktop:")
        print("  macOS: Download from https://docker.com")
        print("  Linux: sudo apt install docker.io docker-compose")
        print("  Windows: Download Docker Desktop")
        return False
    
    print("✅ Docker is running")
    
    # Create .env file
    create_env_file()
    
    # Install Python dependencies
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Start Docker services: docker-compose up")
    print("2. Run tests: pytest")
    print("3. Access API docs: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = setup_local_development()
    sys.exit(0 if success else 1)
