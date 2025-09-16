"""Custom exception classes for the application."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseApplicationError(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ServiceError(BaseApplicationError):
    """Service layer error."""
    pass


class ValidationError(BaseApplicationError):
    """Data validation error."""
    pass


class NotFoundError(BaseApplicationError):
    """Resource not found error."""
    pass


class ConflictError(BaseApplicationError):
    """Resource conflict error."""
    pass


class AuthenticationError(BaseApplicationError):
    """Authentication error."""
    pass


class AuthorizationError(BaseApplicationError):
    """Authorization error."""
    pass


class BusinessLogicError(BaseApplicationError):
    """Business logic violation error."""
    pass


class ExternalServiceError(BaseApplicationError):
    """External service communication error."""
    pass


class RateLimitError(BaseApplicationError):
    """Rate limit exceeded error."""
    pass


# HTTP Exception mappers

def create_http_exception(error: BaseApplicationError) -> HTTPException:
    """Create FastAPI HTTPException from application error."""
    
    error_mapping = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        BusinessLogicError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        ServiceError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = error_mapping.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "message": error.message,
            "details": error.details,
            "error_type": type(error).__name__
        }
    )


# Specific business logic exceptions

class BookingConflictError(ConflictError):
    """Booking time conflict error."""
    pass


class InsufficientSlotsError(BusinessLogicError):
    """No available slots error."""
    pass


class BookingNotCancellableError(BusinessLogicError):
    """Booking cannot be cancelled error."""
    pass


class InvalidTimeRangeError(ValidationError):
    """Invalid time range error."""
    pass


class ParkingLotNotActiveError(BusinessLogicError):
    """Parking lot is not active error."""
    pass


class SlotNotAvailableError(BusinessLogicError):
    """Parking slot is not available error."""
    pass


class UserNotActiveError(BusinessLogicError):
    """User account is not active error."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid login credentials error."""
    pass


class TokenExpiredError(AuthenticationError):
    """Authentication token expired error."""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions error."""
    pass
