"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.auth import AuthService
from app.schemas.auth import (
    UserRegistration,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest
)
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user
from app.models.user import User
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user."""
    try:
        auth_service = AuthService(session)
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone
        )
        return UserResponse.from_orm(user)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """Authenticate user and return tokens."""
    try:
        auth_service = AuthService(session)
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        
        # Create login response with tokens
        response = await auth_service.create_login_response(user)
        return TokenResponse(**response)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Refresh access token using refresh token."""
    try:
        auth_service = AuthService(session)
        
        # Generate new access token
        new_access_token = await auth_service.refresh_access_token(
            refresh_data.refresh_token
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Change user password."""
    try:
        auth_service = AuthService(session)
        
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client-side token invalidation)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse.from_orm(current_user)
