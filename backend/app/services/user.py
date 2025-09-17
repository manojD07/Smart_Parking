"""User service for user management operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.repositories.user import UserRepository
from app.models.user import User
from app.core.exceptions import ValidationError, NotFoundError
import structlog

logger = structlog.get_logger(__name__)


class UserService(BaseService[User, UserRepository]):
    """Service for user management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)
        super().__init__(self.user_repository)
        self.logger = logger.bind(service="UserService")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.user_repository.get_by_email(email)
    
    async def get_active_user_by_email(self, email: str) -> Optional[User]:
        """Get active user by email address."""
        return await self.user_repository.get_active_user_by_email(email)
    
    async def search_users(self, search_term: str, skip: int = 0, limit: int = 20) -> List[User]:
        """Search users by name or email."""
        return await self.user_repository.search_users(search_term, skip, limit)
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user account."""
        return await self.user_repository.deactivate_user(user_id)
    
    async def activate_user(self, user_id: UUID) -> bool:
        """Activate user account."""
        return await self.user_repository.activate_user(user_id)
    
    async def get_all_users_admin(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_admin: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get all users for admin with filtering options."""
        return await self.user_repository.get_all_users_admin(
            skip=skip,
            limit=limit,
            search=search,
            is_admin=is_admin,
            is_active=is_active
        )
    
    def _get_entity_name(self) -> str:
        """Get entity name for base service."""
        return "User"
