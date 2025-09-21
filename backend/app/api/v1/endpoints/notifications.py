"""Notification API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_async_session
from app.models.user import User
from app.models.notification import NotificationType
from app.services.notification_enhanced import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationStatsResponse,
    NotificationUpdate,
    MarkAllReadRequest,
    BulkNotificationAction,
    NotificationCreate
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_user_notifications(
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get notifications for the current user with pagination and filtering."""
    try:
        notification_service = NotificationService(session)
        
        # Get notifications
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            notification_type=notification_type
        )
        
        # Get total count for pagination
        stats = await notification_service.get_notification_stats(current_user.id)
        total = stats["unread_count"] if unread_only else stats["total_notifications"]
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        # Convert to response format using model's to_dict method
        notification_responses = [
            notification.to_dict()
            for notification in notifications
        ]
        
        logger.info(
            "Retrieved user notifications",
            user_id=str(current_user.id),
            count=len(notifications),
            total=total,
            unread_only=unread_only
        )
        
        return {
            "notifications": notification_responses,
            "total": total,
            "page": page,
            "size": limit,
            "pages": pages
        }
        
    except Exception as e:
        logger.error("Failed to get user notifications", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get notification statistics for the current user."""
    try:
        notification_service = NotificationService(session)
        stats = await notification_service.get_notification_stats(current_user.id)
        
        logger.debug("Retrieved notification stats", user_id=str(current_user.id), stats=stats)
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get notification stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics"
        )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Mark a specific notification as read."""
    try:
        notification_service = NotificationService(session)
        
        success = await notification_service.mark_as_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or not owned by user"
            )
        
        logger.info(
            "Notification marked as read",
            notification_id=str(notification_id),
            user_id=str(current_user.id)
        )
        
        return {"message": "Notification marked as read", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark notification as read", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Mark all notifications as read for the current user."""
    try:
        notification_service = NotificationService(session)
        
        updated_count = await notification_service.mark_all_as_read(current_user.id)
        
        logger.info(
            "Marked all notifications as read",
            user_id=str(current_user.id),
            updated_count=updated_count
        )
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count,
            "success": True
        }
        
    except Exception as e:
        logger.error("Failed to mark all notifications as read", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a specific notification."""
    try:
        notification_service = NotificationService(session)
        
        success = await notification_service.delete_notification(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or not owned by user"
            )
        
        logger.info(
            "Notification deleted",
            notification_id=str(notification_id),
            user_id=str(current_user.id)
        )
        
        return {"message": "Notification deleted successfully", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete notification", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific notification by ID."""
    try:
        notification_service = NotificationService(session)
        
        notification = await notification_service.get_by_id(notification_id)
        
        if not notification or notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or not owned by user"
            )
        
        logger.debug(
            "Retrieved notification",
            notification_id=str(notification_id),
            user_id=str(current_user.id)
        )
        
        return notification.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get notification", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification"
        )


@router.post("/bulk-action")
async def bulk_notification_action(
    action_request: BulkNotificationAction,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Perform bulk actions on multiple notifications."""
    try:
        notification_service = NotificationService(session)
        
        success_count = 0
        failed_count = 0
        
        for notification_id in action_request.notification_ids:
            try:
                if action_request.action == "read":
                    success = await notification_service.mark_as_read(notification_id, current_user.id)
                elif action_request.action == "unread":
                    # TODO: Implement mark as unread functionality
                    success = False
                elif action_request.action == "delete":
                    success = await notification_service.delete_notification(notification_id, current_user.id)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid action: {action_request.action}"
                    )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(
                    "Failed to process notification in bulk action",
                    notification_id=str(notification_id),
                    action=action_request.action,
                    error=str(e)
                )
                failed_count += 1
        
        logger.info(
            "Bulk notification action completed",
            user_id=str(current_user.id),
            action=action_request.action,
            total=len(action_request.notification_ids),
            success_count=success_count,
            failed_count=failed_count
        )
        
        return {
            "message": f"Bulk {action_request.action} completed",
            "total": len(action_request.notification_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "success": failed_count == 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to perform bulk notification action", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )


# Admin endpoints (future enhancement)
@router.post("/admin/create", response_model=NotificationResponse)
async def create_notification_admin(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a notification (admin only - for testing/future use)."""
    # For now, allow any authenticated user to create notifications for testing
    # TODO: Add admin-only check when admin role system is implemented
    
    try:
        notification_service = NotificationService(session)
        
        notification = await notification_service.create_notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            priority=notification_data.priority,
            scheduled_at=notification_data.scheduled_at,
            booking_id=notification_data.booking_id,
            lot_id=notification_data.lot_id,
            send_email=notification_data.send_email,
            send_sms=notification_data.send_sms,
            send_push=notification_data.send_push,
            send_websocket=notification_data.send_websocket
        )
        
        logger.info(
            "Notification created via admin endpoint",
            notification_id=str(notification.id),
            created_by=str(current_user.id),
            target_user=str(notification_data.user_id)
        )
        
        return notification.to_dict()
        
    except Exception as e:
        logger.error("Failed to create notification via admin endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )
