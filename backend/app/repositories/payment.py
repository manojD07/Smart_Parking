"""Payment repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.payment import Payment, PaymentTransaction, PaymentCard, PaymentStatus, PaymentMethod
from app.models.user import User
from app.models.booking import Booking


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        result = await self.session.execute(
            select(Payment)
            .options(
                selectinload(Payment.user),
                selectinload(Payment.booking),
                selectinload(Payment.transactions)
            )
            .where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_gateway_transaction_id(self, gateway_transaction_id: str) -> Optional[Payment]:
        """Get payment by gateway transaction ID."""
        result = await self.session.execute(
            select(Payment)
            .options(
                selectinload(Payment.user),
                selectinload(Payment.booking),
                selectinload(Payment.transactions)
            )
            .where(Payment.gateway_transaction_id == gateway_transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_payments(
        self,
        user_id: UUID,
        status: Optional[PaymentStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Payment]:
        """Get payments for a specific user."""
        query = select(Payment).options(
            selectinload(Payment.booking),
            selectinload(Payment.transactions)
        ).where(Payment.user_id == user_id)
        
        if status:
            query = query.where(Payment.status == status.value)
        
        query = query.order_by(desc(Payment.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_booking_payments(self, booking_id: UUID) -> List[Payment]:
        """Get all payments for a specific booking."""
        result = await self.session.execute(
            select(Payment)
            .options(
                selectinload(Payment.user),
                selectinload(Payment.transactions)
            )
            .where(Payment.booking_id == booking_id)
            .order_by(desc(Payment.created_at))
        )
        return list(result.scalars().all())
    
    async def get_pending_payments(self, older_than_minutes: int = 30) -> List[Payment]:
        """Get payments that are pending for more than specified minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        
        result = await self.session.execute(
            select(Payment)
            .where(
                and_(
                    Payment.status == PaymentStatus.PENDING.value,
                    Payment.created_at < cutoff_time
                )
            )
            .order_by(asc(Payment.created_at))
        )
        return list(result.scalars().all())
    
    async def get_expired_payments(self) -> List[Payment]:
        """Get payments that have expired."""
        now = datetime.utcnow()
        
        result = await self.session.execute(
            select(Payment)
            .where(
                and_(
                    Payment.expires_at.isnot(None),
                    Payment.expires_at < now,
                    Payment.status.in_([PaymentStatus.PENDING.value, PaymentStatus.PROCESSING.value])
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_payments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        payment_method: Optional[PaymentMethod] = None,
        status: Optional[PaymentStatus] = None,
        user_id: Optional[UUID] = None
    ) -> List[Payment]:
        """Get payments within a date range with optional filters."""
        query = select(Payment).options(
            selectinload(Payment.user),
            selectinload(Payment.booking)
        ).where(
            and_(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date
            )
        )
        
        if payment_method:
            query = query.where(Payment.payment_method == payment_method.value)
        
        if status:
            query = query.where(Payment.status == status.value)
        
        if user_id:
            query = query.where(Payment.user_id == user_id)
        
        query = query.order_by(desc(Payment.created_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_payment_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get payment statistics for a date range."""
        base_query = select(Payment).where(
            and_(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date
            )
        )
        
        if user_id:
            base_query = base_query.where(Payment.user_id == user_id)
        
        # Total payments and amount
        total_result = await self.session.execute(
            select(
                func.count(Payment.id).label('total_count'),
                func.coalesce(func.sum(Payment.amount), 0).label('total_amount')
            ).select_from(base_query.subquery())
        )
        total_stats = total_result.first()
        
        # Status breakdown
        status_result = await self.session.execute(
            select(
                Payment.status,
                func.count(Payment.id).label('count'),
                func.coalesce(func.sum(Payment.amount), 0).label('amount')
            )
            .select_from(base_query.subquery())
            .group_by(Payment.status)
        )
        status_breakdown = {row.status: {'count': row.count, 'amount': float(row.amount)} 
                          for row in status_result.all()}
        
        # Payment method breakdown
        method_result = await self.session.execute(
            select(
                Payment.payment_method,
                func.count(Payment.id).label('count'),
                func.coalesce(func.sum(Payment.amount), 0).label('amount')
            )
            .select_from(base_query.subquery())
            .group_by(Payment.payment_method)
        )
        method_breakdown = {row.payment_method: {'count': row.count, 'amount': float(row.amount)} 
                          for row in method_result.all()}
        
        # Total refunds
        refund_result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.refund_amount), 0))
            .select_from(base_query.subquery())
        )
        total_refunds = refund_result.scalar() or 0
        
        return {
            'total_payments': total_stats.total_count or 0,
            'total_amount': float(total_stats.total_amount or 0),
            'total_refunds': float(total_refunds),
            'status_breakdown': status_breakdown,
            'method_breakdown': method_breakdown,
            'success_rate': self._calculate_success_rate(status_breakdown, total_stats.total_count or 0)
        }
    
    async def get_daily_payment_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily payment statistics."""
        result = await self.session.execute(
            select(
                func.date(Payment.created_at).label('date'),
                func.count(Payment.id).label('count'),
                func.coalesce(func.sum(Payment.amount), 0).label('amount'),
                func.count(
                    func.case((Payment.status == PaymentStatus.COMPLETED.value, 1), else_=None)
                ).label('successful_count')
            )
            .where(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date
                )
            )
            .group_by(func.date(Payment.created_at))
            .order_by(func.date(Payment.created_at))
        )
        
        return [
            {
                'date': row.date,
                'count': row.count,
                'amount': float(row.amount),
                'successful_count': row.successful_count,
                'success_rate': (row.successful_count / row.count * 100) if row.count > 0 else 0
            }
            for row in result.all()
        ]
    
    async def get_top_users_by_payment_volume(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by payment volume."""
        result = await self.session.execute(
            select(
                Payment.user_id,
                User.email,
                User.first_name,
                User.last_name,
                func.count(Payment.id).label('payment_count'),
                func.coalesce(func.sum(Payment.amount), 0).label('total_amount')
            )
            .join(User, Payment.user_id == User.id)
            .where(
                and_(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == PaymentStatus.COMPLETED.value
                )
            )
            .group_by(Payment.user_id, User.email, User.first_name, User.last_name)
            .order_by(desc(func.sum(Payment.amount)))
            .limit(limit)
        )
        
        return [
            {
                'user_id': str(row.user_id),
                'email': row.email,
                'name': f"{row.first_name} {row.last_name}",
                'payment_count': row.payment_count,
                'total_amount': float(row.total_amount)
            }
            for row in result.all()
        ]
    
    def _calculate_success_rate(self, status_breakdown: Dict[str, Dict], total_count: int) -> float:
        """Calculate payment success rate."""
        if total_count == 0:
            return 0.0
        
        successful_count = status_breakdown.get(PaymentStatus.COMPLETED.value, {}).get('count', 0)
        return (successful_count / total_count) * 100


class PaymentTransactionRepository(BaseRepository[PaymentTransaction]):
    """Repository for payment transaction operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PaymentTransaction, session)
    
    async def get_payment_transactions(self, payment_id: UUID) -> List[PaymentTransaction]:
        """Get all transactions for a payment."""
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.payment_id == payment_id)
            .order_by(desc(PaymentTransaction.created_at))
        )
        return list(result.scalars().all())
    
    async def get_by_gateway_transaction_id(self, gateway_transaction_id: str) -> Optional[PaymentTransaction]:
        """Get transaction by gateway transaction ID."""
        result = await self.session.execute(
            select(PaymentTransaction)
            .options(selectinload(PaymentTransaction.payment))
            .where(PaymentTransaction.gateway_transaction_id == gateway_transaction_id)
        )
        return result.scalar_one_or_none()


class PaymentCardRepository(BaseRepository[PaymentCard]):
    """Repository for payment card operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PaymentCard, session)
    
    async def get_user_cards(self, user_id: UUID, active_only: bool = True) -> List[PaymentCard]:
        """Get all cards for a user."""
        query = select(PaymentCard).where(PaymentCard.user_id == user_id)
        
        if active_only:
            query = query.where(PaymentCard.is_active == True)
        
        query = query.order_by(desc(PaymentCard.is_default), desc(PaymentCard.created_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_default_card(self, user_id: UUID) -> Optional[PaymentCard]:
        """Get user's default card."""
        result = await self.session.execute(
            select(PaymentCard)
            .where(
                and_(
                    PaymentCard.user_id == user_id,
                    PaymentCard.is_default == True,
                    PaymentCard.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_token(self, card_token: str) -> Optional[PaymentCard]:
        """Get card by token."""
        result = await self.session.execute(
            select(PaymentCard)
            .options(selectinload(PaymentCard.user))
            .where(PaymentCard.card_token == card_token)
        )
        return result.scalar_one_or_none()
    
    async def set_default_card(self, user_id: UUID, card_id: UUID) -> None:
        """Set a card as default (and unset others)."""
        # First, unset all default cards for the user
        await self.session.execute(
            select(PaymentCard)
            .where(PaymentCard.user_id == user_id)
            .update({'is_default': False})
        )
        
        # Then set the specified card as default
        await self.session.execute(
            select(PaymentCard)
            .where(
                and_(
                    PaymentCard.user_id == user_id,
                    PaymentCard.id == card_id
                )
            )
            .update({'is_default': True})
        )
    
    async def deactivate_card(self, card_id: UUID, user_id: UUID) -> bool:
        """Deactivate a user's card."""
        result = await self.session.execute(
            select(PaymentCard)
            .where(
                and_(
                    PaymentCard.id == card_id,
                    PaymentCard.user_id == user_id
                )
            )
            .update({'is_active': False, 'is_default': False})
        )
        return result.rowcount > 0
