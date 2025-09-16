"""User schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=2, max_length=50, description="First name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """User update schema."""
    
    first_name: Optional[str] = Field(None, min_length=2, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=2, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")


class UserResponse(UserBase):
    """User response schema."""
    
    id: UUID = Field(..., description="User ID")
    is_admin: bool = Field(..., description="Whether user is admin")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
