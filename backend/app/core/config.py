"""Application configuration management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Application
    app_name: str = "Smart Parking Management System"
    version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    
    # Database
    database_url: str = Field(..., description="Async database URL")
    database_url_sync: str = Field(..., description="Sync database URL for migrations")
    
    # Redis
    redis_url: str = Field(..., description="Redis URL")
    
    # JWT
    secret_key: str = Field(..., description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:4200"], 
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")
    
    # Booking Configuration
    max_booking_duration_hours: int = Field(default=24, description="Max booking duration")
    booking_expiry_minutes: int = Field(default=10, description="Booking expiry time")
    
    # Celery
    celery_broker_url: str = Field(..., description="Celery broker URL")
    celery_result_backend: str = Field(..., description="Celery result backend")
    
    # Pagination
    default_page_size: int = Field(default=20, description="Default pagination size")
    max_page_size: int = Field(default=100, description="Maximum pagination size")
    
    # Slot time chunks
    slot_time_chunk_size: int = Field(default=30, description="Time chunk size in minutes")
    
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
