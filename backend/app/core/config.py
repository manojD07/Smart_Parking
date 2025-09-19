"""Application configuration management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict
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
    
    # Smart chunk system configuration
    chunk_resolutions: List[int] = Field(
        default=[1, 5, 10, 15, 30, 60, 120, 240], 
        description="Available chunk sizes in minutes"
    )
    default_chunk_size: int = Field(default=15, description="Default chunk size in minutes")
    min_chunk_size: int = Field(default=1, description="Minimum chunk size in minutes")
    max_chunk_size: int = Field(default=240, description="Maximum chunk size in minutes")
    
    # Demand-based chunk sizing
    demand_chunk_mapping: Dict[str, int] = Field(
        default={
            'low': 30,      # Off-peak: 30-min chunks
            'medium': 15,   # Normal: 15-min chunks
            'high': 5,      # Busy: 5-min chunks
            'peak': 1       # Peak: 1-min precision
        },
        description="Chunk sizes by demand level"
    )
    
    # Hybrid duration constraints
    min_booking_duration: int = Field(default=15, description="Minimum booking duration in minutes")
    max_booking_duration: int = Field(default=1440, description="Maximum booking duration in minutes")
    booking_increment: int = Field(default=5, description="Booking time increment in minutes")
    
    # Buffer time for back-to-back bookings
    enable_buffer_time: bool = Field(default=True, description="Enable buffer time between bookings")
    buffer_time_strategy: str = Field(default="incremental", description="Buffer time strategy: incremental, fixed, or demand_based")
    fixed_buffer_minutes: int = Field(default=5, description="Fixed buffer time in minutes")
    incremental_buffer_enabled: bool = Field(default=True, description="Use tier-based incremental buffer")
    demand_based_buffer: bool = Field(default=False, description="Adjust buffer based on demand")
    
    # Legacy compatibility
    slot_time_chunk_size: int = Field(default=15, description="Default time chunk size (legacy)")
    
    
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

# Function for dependency injection
def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings
