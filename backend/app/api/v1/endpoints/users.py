"""User management endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.user import UserService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse
)
from app.schemas.auth import ChangePasswordRequest
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.api.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user's profile."""
    try:
        user_service = UserService(session)
        
        update_data = user_data.dict(exclude_unset=True)
        updated_user = await user_service.update(current_user.id, **update_data)
        
        return UserResponse.from_orm(updated_user)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_current_user_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Change current user's password."""
    try:
        from app.services.auth import AuthService
        
        auth_service = AuthService(session)
        
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if success:
            return SuccessResponse(message="Password changed successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.delete("/me", response_model=SuccessResponse)
async def deactivate_current_user_account(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Deactivate current user's account."""
    try:
        user_service = UserService(session)
        
        success = await user_service.deactivate_user(current_user.id)
        
        if success:
            return SuccessResponse(message="Account deactivated successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate account"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/me/bookings")
async def get_current_user_bookings(
    status: Optional[str] = Query(None, description="Filter by booking status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's bookings."""
    try:
        from app.services.booking import BookingService
        from app.models.booking import BookingStatus
        from app.schemas.booking import BookingResponse
        
        booking_service = BookingService(session)
        
        booking_status = BookingStatus(status) if status else None
        bookings = await booking_service.get_user_bookings(
            user_id=current_user.id,
            status=booking_status,
            skip=skip,
            limit=limit
        )
        
        return [BookingResponse.from_orm(booking) for booking in bookings]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


# Admin endpoints
@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users (admin only)."""
    try:
        user_service = UserService(session)
        
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if is_admin is not None:
            filters["is_admin"] = is_admin
        
        users = await user_service.get_multi(
            skip=skip,
            limit=limit,
            **filters
        )
        
        return [UserResponse.from_orm(user) for user in users]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID (admin only)."""
    try:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id)
        
        return UserResponse.from_orm(user)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update user (admin only)."""
    try:
        user_service = UserService(session)
        
        update_data = user_data.dict(exclude_unset=True)
        updated_user = await user_service.update(user_id, **update_data)
        
        return UserResponse.from_orm(updated_user)
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{user_id}/activate", response_model=SuccessResponse)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Activate user account (admin only)."""
    try:
        user_service = UserService(session)
        
        success = await user_service.activate_user(user_id)
        
        if success:
            return SuccessResponse(message="User activated successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate user"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{user_id}/deactivate", response_model=SuccessResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Deactivate user account (admin only)."""
    try:
        user_service = UserService(session)
        
        success = await user_service.deactivate_user(user_id)
        
        if success:
            return SuccessResponse(message="User deactivated successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate user"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{user_id}/make-admin", response_model=SuccessResponse)
async def make_user_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Grant admin privileges to user (admin only)."""
    try:
        user_service = UserService(session)
        
        updated_user = await user_service.update(user_id, is_admin=True)
        
        if updated_user:
            return SuccessResponse(message="User granted admin privileges")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to grant admin privileges"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/{user_id}/remove-admin", response_model=SuccessResponse)
async def remove_user_admin(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove admin privileges from user (admin only)."""
    try:
        user_service = UserService(session)
        
        updated_user = await user_service.update(user_id, is_admin=False)
        
        if updated_user:
            return SuccessResponse(message="Admin privileges removed")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove admin privileges"
            )
            
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Search users (admin only)."""
    try:
        user_service = UserService(session)
        
        users = await user_service.search_users(
            search_term=q,
            skip=skip,
            limit=limit
        )
        
        return [UserResponse.from_orm(user) for user in users]
        
    except BaseApplicationError as e:
        raise create_http_exception(e)