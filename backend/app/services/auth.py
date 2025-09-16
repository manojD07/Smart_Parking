"""Authentication service for handling user authentication and authorization."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError, 
    ValidationError, 
    InvalidCredentialsError,
    TokenExpiredError,
    UserNotActiveError
)
from app.repositories.user import UserRepository
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)


class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)
        self.logger = logger.bind(service="AuthService")
    
    async def register_user(
        self, 
        email: str, 
        password: str, 
        first_name: str, 
        last_name: str,
        phone: Optional[str] = None
    ) -> User:
        """Register a new user."""
        try:
            # Validate input
            await self._validate_registration_data(email, password, first_name, last_name)
            
            # Check if email already exists
            if await self.user_repository.is_email_taken(email):
                raise ValidationError("Email address already registered")
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user = await self.user_repository.create(
                email=email.lower().strip(),
                password_hash=password_hash,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone=phone.strip() if phone else None
            )
            
            self.logger.info("User registered successfully", user_id=user.id, email=email)
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error("Failed to register user", email=email, error=str(e))
            raise AuthenticationError("Registration failed")
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        try:
            # Get user by email
            user = await self.user_repository.get_by_email(email.lower().strip())
            if not user:
                raise InvalidCredentialsError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise UserNotActiveError("User account is deactivated")
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                raise InvalidCredentialsError("Invalid email or password")
            
            self.logger.info("User authenticated successfully", user_id=user.id, email=email)
            return user
            
        except (InvalidCredentialsError, UserNotActiveError):
            raise
        except Exception as e:
            self.logger.error("Failed to authenticate user", email=email, error=str(e))
            raise AuthenticationError("Authentication failed")
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        try:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
            
            payload = {
                "sub": str(user.id),
                "email": user.email,
                "is_admin": user.is_admin,
                "exp": expire,
                "type": "access"
            }
            
            token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
            
            self.logger.info("Access token created", user_id=user.id)
            return token
            
        except Exception as e:
            self.logger.error("Failed to create access token", user_id=user.id, error=str(e))
            raise AuthenticationError("Failed to create access token")
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user."""
        try:
            expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
            
            payload = {
                "sub": str(user.id),
                "exp": expire,
                "type": "refresh"
            }
            
            token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
            
            self.logger.info("Refresh token created", user_id=user.id)
            return token
            
        except Exception as e:
            self.logger.error("Failed to create refresh token", user_id=user.id, error=str(e))
            raise AuthenticationError("Failed to create refresh token")
    
    async def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise TokenExpiredError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise TokenExpiredError("Token has expired")
            
            return payload
            
        except JWTError as e:
            self.logger.warning("Invalid token", error=str(e))
            raise TokenExpiredError("Invalid or expired token")
        except Exception as e:
            self.logger.error("Failed to verify token", error=str(e))
            raise AuthenticationError("Token verification failed")
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = await self.verify_token(token)
            user_id = UUID(payload.get("sub"))
            
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise InvalidCredentialsError("User not found")
            
            if not user.is_active:
                raise UserNotActiveError("User account is deactivated")
            
            return user
            
        except (InvalidCredentialsError, UserNotActiveError, TokenExpiredError):
            raise
        except Exception as e:
            self.logger.error("Failed to get current user", error=str(e))
            raise AuthenticationError("Failed to get current user")
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token."""
        try:
            payload = await self.verify_token(refresh_token, "refresh")
            user_id = UUID(payload.get("sub"))
            
            user = await self.user_repository.get_by_id(user_id)
            if not user or not user.is_active:
                raise InvalidCredentialsError("Invalid refresh token")
            
            return self.create_access_token(user)
            
        except (InvalidCredentialsError, TokenExpiredError):
            raise
        except Exception as e:
            self.logger.error("Failed to refresh access token", error=str(e))
            raise AuthenticationError("Failed to refresh access token")
    
    async def change_password(
        self, 
        user_id: UUID, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password."""
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise InvalidCredentialsError("User not found")
            
            # Verify current password
            if not self._verify_password(current_password, user.password_hash):
                raise InvalidCredentialsError("Current password is incorrect")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Hash new password
            new_password_hash = self._hash_password(new_password)
            
            # Update password
            updated = await self.user_repository.update_password(user_id, new_password_hash)
            
            if updated:
                self.logger.info("Password changed successfully", user_id=user_id)
            
            return updated
            
        except (InvalidCredentialsError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Failed to change password", user_id=user_id, error=str(e))
            raise AuthenticationError("Failed to change password")
    
    async def reset_password(self, email: str, new_password: str) -> bool:
        """Reset user password (admin function)."""
        try:
            user = await self.user_repository.get_by_email(email.lower().strip())
            if not user:
                raise InvalidCredentialsError("User not found")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Hash new password
            new_password_hash = self._hash_password(new_password)
            
            # Update password
            updated = await self.user_repository.update_password(user.id, new_password_hash)
            
            if updated:
                self.logger.info("Password reset successfully", user_id=user.id)
            
            return updated
            
        except (InvalidCredentialsError, ValidationError):
            raise
        except Exception as e:
            self.logger.error("Failed to reset password", email=email, error=str(e))
            raise AuthenticationError("Failed to reset password")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def _validate_registration_data(
        self, 
        email: str, 
        password: str, 
        first_name: str, 
        last_name: str
    ) -> None:
        """Validate user registration data."""
        # Email validation
        if not email or len(email.strip()) < 5:
            raise ValidationError("Valid email address is required")
        
        if '@' not in email or '.' not in email:
            raise ValidationError("Invalid email format")
        
        # Password validation
        self._validate_password(password)
        
        # Name validation
        if not first_name or len(first_name.strip()) < 2:
            raise ValidationError("First name must be at least 2 characters")
        
        if not last_name or len(last_name.strip()) < 2:
            raise ValidationError("Last name must be at least 2 characters")
    
    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        if not password:
            raise ValidationError("Password is required")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")
        
        # Check for special characters
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        if not any(c in special_chars for c in password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    async def create_login_response(self, user: User) -> Dict[str, Any]:
        """Create complete login response with tokens and user info."""
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin,
                "is_active": user.is_active
            }
        }
