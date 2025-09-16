"""User repository for user-specific database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID

from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            query = select(User).where(User.email == email)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get user by email", email=email, error=str(e))
            raise
    
    async def get_active_user_by_email(self, email: str) -> Optional[User]:
        """Get active user by email address."""
        try:
            query = select(User).where(
                and_(
                    User.email == email,
                    User.is_active == True
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get active user by email", email=email, error=str(e))
            raise
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number."""
        try:
            query = select(User).where(User.phone == phone)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error("Failed to get user by phone", phone=phone, error=str(e))
            raise
    
    async def get_admins(self) -> List[User]:
        """Get all admin users."""
        try:
            query = select(User).where(
                and_(
                    User.is_admin == True,
                    User.is_active == True
                )
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get admin users", error=str(e))
            raise
    
    async def get_users_with_bookings(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users with their bookings loaded."""
        try:
            query = (
                select(User)
                .options(selectinload(User.bookings))
                .where(User.is_active == True)
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to get users with bookings", error=str(e))
            raise
    
    async def search_users(self, search_term: str, skip: int = 0, limit: int = 20) -> List[User]:
        """Search users by name or email."""
        try:
            search_pattern = f"%{search_term}%"
            query = select(User).where(
                and_(
                    User.is_active == True,
                    or_(
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern),
                        User.email.ilike(search_pattern)
                    )
                )
            ).offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error("Failed to search users", search_term=search_term, error=str(e))
            raise
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user instead of deleting."""
        try:
            updated_user = await self.update(user_id, is_active=False)
            return updated_user is not None
            
        except Exception as e:
            self.logger.error("Failed to deactivate user", user_id=user_id, error=str(e))
            raise
    
    async def activate_user(self, user_id: UUID) -> bool:
        """Activate user account."""
        try:
            updated_user = await self.update(user_id, is_active=True)
            return updated_user is not None
            
        except Exception as e:
            self.logger.error("Failed to activate user", user_id=user_id, error=str(e))
            raise
    
    async def update_password(self, user_id: UUID, password_hash: str) -> bool:
        """Update user password."""
        try:
            updated_user = await self.update(user_id, password_hash=password_hash)
            return updated_user is not None
            
        except Exception as e:
            self.logger.error("Failed to update password", user_id=user_id, error=str(e))
            raise
    
    async def is_email_taken(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """Check if email is already taken by another user."""
        try:
            query = select(User).where(User.email == email)
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()
            
            return user is not None
            
        except Exception as e:
            self.logger.error("Failed to check email availability", email=email, error=str(e))
            raise
    
    def _add_relationship_loading(self, query):
        """Add relationship loading for user queries."""
        return query.options(selectinload(User.bookings))
