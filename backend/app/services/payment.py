"""Payment service for processing transactions."""

import asyncio
import secrets
import string
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payment import PaymentRepository, PaymentTransactionRepository, PaymentCardRepository
from app.repositories.user import UserRepository
from app.repositories.booking import BookingRepository
from app.models.payment import (
    Payment, PaymentTransaction, PaymentCard, PaymentStatus, PaymentMethod, 
    PaymentGateway, TransactionType
)
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, RefundRequest, PaymentProcessResponse,
    DummyGatewayResponse, PaymentStats, PaymentCardCreate
)
from app.core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from app.services.base import BaseService
import structlog

logger = structlog.get_logger(__name__)


class DummyPaymentGateway:
    """Dummy payment gateway for testing purposes."""
    
    def __init__(self):
        self.name = "DummyPay Gateway"
        self.version = "1.0.0"
    
    async def process_payment(
        self, 
        amount: Decimal, 
        currency: str, 
        payment_method: str,
        card_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DummyGatewayResponse:
        """Process payment through dummy gateway."""
        
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        # Generate dummy transaction details
        transaction_id = self._generate_transaction_id()
        reference_number = self._generate_reference_number()
        
        # Simulate different success rates based on amount
        success_probability = self._calculate_success_probability(amount)
        success = secrets.SystemRandom().random() < success_probability
        
        if success:
            gateway_fees = self._calculate_gateway_fees(amount)
            return DummyGatewayResponse(
                success=True,
                transaction_id=transaction_id,
                reference_number=reference_number,
                amount=amount,
                currency=currency,
                status="completed",
                message="Payment processed successfully",
                processed_at=datetime.now(timezone.utc),
                gateway_fees=gateway_fees
            )
        else:
            failure_reasons = [
                "Insufficient funds",
                "Card declined",
                "Invalid card details",
                "Network timeout",
                "Bank authentication failed"
            ]
            failure_reason = secrets.choice(failure_reasons)
            
            return DummyGatewayResponse(
                success=False,
                transaction_id=transaction_id,
                reference_number=reference_number,
                amount=amount,
                currency=currency,
                status="failed",
                message=f"Payment failed: {failure_reason}",
                processed_at=datetime.now(timezone.utc),
                gateway_fees=None
            )
    
    async def process_refund(
        self, 
        original_transaction_id: str,
        refund_amount: Decimal, 
        currency: str,
        reason: str
    ) -> DummyGatewayResponse:
        """Process refund through dummy gateway."""
        
        # Simulate processing delay
        await asyncio.sleep(0.3)
        
        # Generate dummy refund details
        transaction_id = self._generate_transaction_id()
        reference_number = self._generate_reference_number()
        
        # Dummy gateway always succeeds refunds
        return DummyGatewayResponse(
            success=True,
            transaction_id=transaction_id,
            reference_number=reference_number,
            amount=refund_amount,
            currency=currency,
            status="completed",
            message=f"Refund processed: {reason}",
            processed_at=datetime.now(timezone.utc),
            gateway_fees=None
        )
    
    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify payment status with gateway."""
        await asyncio.sleep(0.2)
        
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "verified": True,
            "verified_at": datetime.now(timezone.utc)
        }
    
    def _generate_transaction_id(self) -> str:
        """Generate dummy transaction ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"DUMMY{timestamp}{random_part}"
    
    def _generate_reference_number(self) -> str:
        """Generate dummy reference number."""
        return ''.join(secrets.choice(string.digits) for _ in range(12))
    
    def _calculate_success_probability(self, amount: Decimal) -> float:
        """Calculate success probability based on amount."""
        # Higher amounts have slightly lower success rates
        if amount < 10:
            return 0.95
        elif amount < 100:
            return 0.90
        elif amount < 1000:
            return 0.85
        else:
            return 0.80
    
    def _calculate_gateway_fees(self, amount: Decimal) -> Decimal:
        """Calculate gateway processing fees."""
        # 2.9% + $0.30 fee structure
        percentage_fee = amount * Decimal('0.029')
        fixed_fee = Decimal('0.30')
        return percentage_fee + fixed_fee


class PaymentService(BaseService):
    """Service for payment operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.payment_repo = PaymentRepository(session)
        self.transaction_repo = PaymentTransactionRepository(session)
        self.card_repo = PaymentCardRepository(session)
        self.user_repo = UserRepository(session)
        self.booking_repo = BookingRepository(session)
        self.dummy_gateway = DummyPaymentGateway()
    
    async def create_payment(self, user_id: UUID, payment_data: PaymentCreate) -> Payment:
        """Create a new payment."""
        logger.info("Creating payment", user_id=str(user_id), amount=str(payment_data.amount))
        
        # Validate user exists
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate booking if provided
        if payment_data.booking_id:
            booking = await self.booking_repo.get(payment_data.booking_id)
            if not booking:
                raise NotFoundError("Booking not found")
            if booking.user_id != user_id:
                raise ValidationError("Booking does not belong to user")
        
        # Generate transaction ID
        transaction_id = Payment.generate_transaction_id()
        
        # Set expiration time (30 minutes for pending payments)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        # Create payment
        payment = Payment(
            user_id=user_id,
            booking_id=payment_data.booking_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_method=payment_data.payment_method.value,
            payment_gateway=payment_data.payment_gateway.value,
            status=PaymentStatus.PENDING.value,
            transaction_id=transaction_id,
            description=payment_data.description,
            payment_metadata=payment_data.metadata,
            expires_at=expires_at
        )
        
        await self.payment_repo.create(payment)
        logger.info("Payment created", payment_id=str(payment.id), transaction_id=transaction_id)
        
        return payment
    
    async def process_payment(self, payment_id: UUID, gateway_data: Optional[Dict[str, Any]] = None) -> PaymentProcessResponse:
        """Process a payment through the gateway."""
        logger.info("Processing payment", payment_id=str(payment_id))
        
        payment = await self.payment_repo.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        
        if payment.status != PaymentStatus.PENDING.value:
            raise BusinessLogicError(f"Payment is not in pending status: {payment.status}")
        
        if payment.is_expired:
            payment.mark_cancelled()
            await self.payment_repo.update(payment.id, payment)
            raise BusinessLogicError("Payment has expired")
        
        # Mark as processing
        payment.mark_processing()
        await self.payment_repo.update(payment.id, payment)
        
        try:
            # Process through gateway
            if payment.payment_gateway == PaymentGateway.DUMMY_GATEWAY.value:
                gateway_response = await self.dummy_gateway.process_payment(
                    amount=payment.amount,
                    currency=payment.currency,
                    payment_method=payment.payment_method,
                    card_data=gateway_data,
                    metadata=payment.payment_metadata
                )
            else:
                raise BusinessLogicError(f"Unsupported payment gateway: {payment.payment_gateway}")
            
            # Create transaction record
            transaction = PaymentTransaction(
                payment_id=payment.id,
                transaction_type=TransactionType.PAYMENT.value,
                amount=payment.amount,
                status=PaymentStatus.COMPLETED.value if gateway_response.success else PaymentStatus.FAILED.value,
                gateway_response=gateway_response.dict(),
                gateway_transaction_id=gateway_response.transaction_id,
                reference_number=gateway_response.reference_number,
                processed_at=gateway_response.processed_at
            )
            await self.transaction_repo.create(transaction)
            
            # Update payment based on gateway response
            if gateway_response.success:
                payment.mark_completed(
                    gateway_transaction_id=gateway_response.transaction_id,
                    gateway_reference=gateway_response.reference_number
                )
                message = "Payment processed successfully"
            else:
                payment.mark_failed(gateway_response.message)
                message = gateway_response.message
            
            await self.payment_repo.update(payment.id, payment)
            
            logger.info(
                "Payment processing completed",
                payment_id=str(payment.id),
                success=gateway_response.success,
                gateway_transaction_id=gateway_response.transaction_id
            )
            
            return PaymentProcessResponse(
                success=gateway_response.success,
                payment=payment,
                gateway_response=gateway_response.dict(),
                message=message
            )
            
        except Exception as e:
            # Mark payment as failed
            payment.mark_failed(str(e))
            await self.payment_repo.update(payment.id, payment)
            
            logger.error("Payment processing failed", payment_id=str(payment.id), error=str(e))
            raise BusinessLogicError(f"Payment processing failed: {str(e)}")
    
    async def process_refund(self, payment_id: UUID, refund_request: RefundRequest, admin_user_id: UUID) -> Payment:
        """Process a refund for a payment."""
        logger.info("Processing refund", payment_id=str(payment_id), amount=str(refund_request.amount))
        
        payment = await self.payment_repo.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        
        if not payment.is_completed:
            raise BusinessLogicError("Can only refund completed payments")
        
        if refund_request.amount > payment.refundable_amount:
            raise ValidationError(f"Refund amount exceeds refundable amount: {payment.refundable_amount}")
        
        try:
            # Process refund through gateway
            if payment.payment_gateway == PaymentGateway.DUMMY_GATEWAY.value:
                gateway_response = await self.dummy_gateway.process_refund(
                    original_transaction_id=payment.gateway_transaction_id,
                    refund_amount=refund_request.amount,
                    currency=payment.currency,
                    reason=refund_request.reason
                )
            else:
                raise BusinessLogicError(f"Unsupported payment gateway: {payment.payment_gateway}")
            
            if gateway_response.success:
                # Create refund transaction record
                refund_transaction = PaymentTransaction(
                    payment_id=payment.id,
                    transaction_type=TransactionType.REFUND.value if refund_request.amount == payment.amount else TransactionType.PARTIAL_REFUND.value,
                    amount=-refund_request.amount,  # Negative for refunds
                    status=PaymentStatus.COMPLETED.value,
                    gateway_response=gateway_response.dict(),
                    gateway_transaction_id=gateway_response.transaction_id,
                    reference_number=gateway_response.reference_number,
                    notes=f"Refund: {refund_request.reason}",
                    processed_at=gateway_response.processed_at
                )
                await self.transaction_repo.create(refund_transaction)
                
                # Update payment refund amount and status
                payment.add_refund(float(refund_request.amount))
                await self.payment_repo.update(payment.id, payment)
                
                logger.info(
                    "Refund processed successfully",
                    payment_id=str(payment.id),
                    refund_amount=str(refund_request.amount),
                    gateway_transaction_id=gateway_response.transaction_id
                )
                
                return payment
            else:
                raise BusinessLogicError(f"Refund failed: {gateway_response.message}")
                
        except Exception as e:
            logger.error("Refund processing failed", payment_id=str(payment.id), error=str(e))
            raise BusinessLogicError(f"Refund processing failed: {str(e)}")
    
    async def get_payment_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        return await self.payment_repo.get_by_transaction_id(transaction_id)
    
    async def get_user_payments(
        self, 
        user_id: UUID, 
        status: Optional[PaymentStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Payment]:
        """Get payments for a user."""
        return await self.payment_repo.get_user_payments(user_id, status, skip, limit)
    
    async def get_booking_payments(self, booking_id: UUID) -> List[Payment]:
        """Get all payments for a booking."""
        return await self.payment_repo.get_booking_payments(booking_id)
    
    async def cancel_payment(self, payment_id: UUID, user_id: UUID) -> Payment:
        """Cancel a pending payment."""
        payment = await self.payment_repo.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        
        if payment.user_id != user_id:
            raise ValidationError("Payment does not belong to user")
        
        if payment.status not in [PaymentStatus.PENDING.value, PaymentStatus.PROCESSING.value]:
            raise BusinessLogicError(f"Cannot cancel payment with status: {payment.status}")
        
        payment.mark_cancelled()
        await self.payment_repo.update(payment.id, payment)
        
        logger.info("Payment cancelled", payment_id=str(payment.id))
        return payment
    
    async def expire_old_payments(self) -> int:
        """Expire old pending payments."""
        expired_payments = await self.payment_repo.get_expired_payments()
        count = 0
        
        for payment in expired_payments:
            payment.mark_cancelled()
            await self.payment_repo.update(payment.id, payment)
            count += 1
            
            logger.info("Payment expired", payment_id=str(payment.id))
        
        return count
    
    async def get_payment_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[UUID] = None
    ) -> PaymentStats:
        """Get payment statistics."""
        stats_data = await self.payment_repo.get_payment_statistics(start_date, end_date, user_id)
        
        total_payments = stats_data['total_payments']
        successful_payments = stats_data['status_breakdown'].get(PaymentStatus.COMPLETED.value, {}).get('count', 0)
        failed_payments = stats_data['status_breakdown'].get(PaymentStatus.FAILED.value, {}).get('count', 0)
        pending_payments = stats_data['status_breakdown'].get(PaymentStatus.PENDING.value, {}).get('count', 0)
        
        average_payment = Decimal('0')
        if total_payments > 0:
            average_payment = Decimal(str(stats_data['total_amount'])) / total_payments
        
        return PaymentStats(
            total_payments=total_payments,
            total_amount=Decimal(str(stats_data['total_amount'])),
            successful_payments=successful_payments,
            failed_payments=failed_payments,
            pending_payments=pending_payments,
            total_refunds=Decimal(str(stats_data['total_refunds'])),
            average_payment=average_payment,
            success_rate=stats_data['success_rate']
        )
    
    # Card Management Methods
    
    async def add_payment_card(self, user_id: UUID, card_data: PaymentCardCreate) -> PaymentCard:
        """Add a payment card for a user."""
        logger.info("Adding payment card", user_id=str(user_id))
        
        # Validate user exists
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Generate card token (in real implementation, this would be done by payment gateway)
        card_token = self._generate_card_token()
        
        # Detect card brand and type (simplified logic)
        card_brand, card_type = self._detect_card_details(card_data.card_number)
        
        # Get last 4 digits
        card_last_four = card_data.card_number[-4:]
        
        # If this is set as default, unset other default cards
        if card_data.is_default:
            await self._unset_default_cards(user_id)
        
        # Create card record
        card = PaymentCard(
            user_id=user_id,
            card_token=card_token,
            card_last_four=card_last_four,
            card_brand=card_brand,
            card_type=card_type,
            expiry_month=card_data.expiry_month,
            expiry_year=card_data.expiry_year,
            cardholder_name=card_data.cardholder_name,
            is_default=card_data.is_default,
            is_active=True
        )
        
        await self.card_repo.create(card)
        logger.info("Payment card added", card_id=str(card.id))
        
        return card
    
    async def get_user_cards(self, user_id: UUID) -> List[PaymentCard]:
        """Get all payment cards for a user."""
        return await self.card_repo.get_user_cards(user_id)
    
    async def set_default_card(self, user_id: UUID, card_id: UUID) -> None:
        """Set a card as default."""
        # Verify card belongs to user
        card = await self.card_repo.get(card_id)
        if not card or card.user_id != user_id:
            raise NotFoundError("Card not found")
        
        await self.card_repo.set_default_card(user_id, card_id)
        logger.info("Default card set", user_id=str(user_id), card_id=str(card_id))
    
    async def remove_payment_card(self, user_id: UUID, card_id: UUID) -> bool:
        """Remove a payment card."""
        success = await self.card_repo.deactivate_card(card_id, user_id)
        if success:
            logger.info("Payment card removed", card_id=str(card_id))
        return success
    
    def _generate_card_token(self) -> str:
        """Generate a secure card token."""
        return f"card_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))}"
    
    def _detect_card_details(self, card_number: str) -> Tuple[str, str]:
        """Detect card brand and type from card number."""
        # Simplified card detection logic
        first_digit = card_number[0]
        
        if card_number.startswith('4'):
            return 'visa', 'credit'
        elif card_number.startswith('5') or card_number.startswith('2'):
            return 'mastercard', 'credit'
        elif card_number.startswith('3'):
            return 'amex', 'credit'
        elif card_number.startswith('6'):
            return 'discover', 'credit'
        else:
            return 'unknown', 'credit'
    
    async def _unset_default_cards(self, user_id: UUID) -> None:
        """Unset all default cards for a user."""
        cards = await self.card_repo.get_user_cards(user_id, active_only=False)
        for card in cards:
            if card.is_default:
                card.is_default = False
                await self.card_repo.update(card.id, card)
