"""Payment endpoints."""

from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.booking import BookingService
from app.services.dummy_payment import DummyPaymentService
from app.schemas.payment import DummyPaymentRequest, DummyPaymentResponse, PaymentMethod
from app.schemas.common import SuccessResponse
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.booking import BookingStatus
from app.core.exceptions import create_http_exception, BaseApplicationError

router = APIRouter()


@router.get("/methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get available payment methods."""
    payment_service = DummyPaymentService()
    return {
        "payment_methods": payment_service.get_payment_methods(),
        "supported_currencies": ["USD"],
        "service_charges": {
            "credit_card": 2.5,
            "debit_card": 1.5,
            "upi": 0.0,
            "net_banking": 1.0
        }
    }


@router.post("/process", response_model=DummyPaymentResponse)
async def process_payment(
    payment_request: DummyPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Process a dummy payment for a booking."""
    try:
        booking_service = BookingService(session)
        payment_service = DummyPaymentService()
        
        # Get the booking
        booking = await booking_service.get_by_id(UUID(payment_request.booking_id), load_relationships=True)
        
        # Verify booking belongs to user
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pay for your own bookings"
            )
        
        # Check if booking is in correct status for payment
        if booking.status != BookingStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot process payment for booking with status: {booking.status}"
            )
        
        # Process the payment
        payment_result = await payment_service.process_payment(
            booking=booking,
            payment_method=payment_request.payment_method,
            simulate_failure=payment_request.simulate_failure
        )
        
        # Update booking status based on payment result
        if payment_result.success:
            # Update booking status to CONFIRMED after successful payment
            await booking_service.confirm_booking_after_payment(booking.id)
        
        return payment_result
        
    except BaseApplicationError as e:
        raise create_http_exception(e)


@router.post("/validate", response_model=Dict[str, Any])
async def validate_payment_details(
    payment_method: PaymentMethod,
    payment_details: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Validate payment method details."""
    payment_service = DummyPaymentService()
    
    validation_result = await payment_service.validate_payment_method(
        payment_method=payment_method,
        payment_details=payment_details
    )
    
    return validation_result


@router.get("/booking/{booking_id}/status")
async def get_payment_status(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get payment status for a booking."""
    try:
        booking_service = BookingService(session)
        
        booking = await booking_service.get_by_id(booking_id, load_relationships=True)
        
        # Verify booking belongs to user
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check payment status for your own bookings"
            )
        
        payment_status = "paid" if booking.status in [
            BookingStatus.CONFIRMED.value,
            BookingStatus.ACTIVE.value,
            BookingStatus.COMPLETED.value
        ] else "pending"
        
        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "payment_status": payment_status,
            "booking_status": booking.status,
            "amount": float(booking.total_amount),
            "currency": "USD"
        }
        
    except BaseApplicationError as e:
        raise create_http_exception(e)