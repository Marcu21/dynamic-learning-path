"""
Notifications API Endpoints

This module provides FastAPI endpoints for managing notifications.
"""

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db_session, get_current_active_user
from app.models.user import User
from app.schemas.core_schemas.notification_schema import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    NotificationUpdateResponse,
    NotificationDeletionResponse,
    MarkAllReadResponse,
    NotificationUpdate,
)
from app.services.core_services import notification_service
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# =============================
# NOTIFICATION RETRIEVAL ENDPOINTS
# =============================

@router.get("/", response_model=NotificationListResponse)
async def get_user_notifications(
        include_read: bool = Query(True, description="Include read notifications"),
        include_deleted: bool = Query(False, description="Include deleted notifications"),
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get paginated notifications for the current user
    """
    try:
        notifications_data = await notification_service.get_user_notifications(
            db=db,
            user_id=current_user.id,
            include_read=include_read,
            include_deleted=include_deleted,
            page=page,
            per_page=per_page
        )

        return NotificationListResponse(
            notifications=notifications_data["notifications"],
            total=notifications_data["total"],
            unread_count=notifications_data["unread_count"],
            page=page,
            per_page=per_page,
            has_next=notifications_data["has_next"],
            has_prev=notifications_data["has_prev"]
        )

    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get count of unread notifications
    """
    try:
        unread_count = await notification_service.get_unread_notification_count(
            db=db,
            user_id=current_user.id
        )

        return UnreadCountResponse(unread_count=unread_count)

    except Exception as e:
        logger.error(f"Error getting unread count for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
        notification_id: int = Path(..., description="Notification ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific notification
    """
    try:
        notification = await notification_service.get_notification_by_id(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# NOTIFICATION UPDATE ENDPOINTS
# =============================

@router.patch("/{notification_id}", response_model=NotificationUpdateResponse)
async def update_notification(
        update_data: NotificationUpdate,
        notification_id: int = Path(..., description="Notification ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Update notification (mark as read/deleted via PATCH body)
    Accepts { "is_read": true } or { "is_deleted": true } in request body
    """
    try:
        updated_notification = await notification_service.update_notification(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id,
        )

        if not updated_notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return NotificationUpdateResponse(
            success=True,
            message="Notification updated successfully",
            notification=updated_notification
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_notifications_as_read(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Mark all notifications as read for user
    """
    try:
        marked_count = await notification_service.mark_all_notifications_as_read(
            db=db,
            user_id=current_user.id
        )

        return MarkAllReadResponse(
            success=True,
            message=f"Marked {marked_count} notifications as read",
            marked_count=marked_count
        )

    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# NOTIFICATION DELETION ENDPOINTS
# =============================

@router.delete("/{notification_id}", response_model=NotificationDeletionResponse)
async def delete_notification(
        notification_id: int = Path(..., description="Notification ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a specific notification (soft delete)
    """
    try:
        success = await notification_service.delete_notification(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return NotificationDeletionResponse(
            success=True,
            message="Notification deleted successfully",
            deleted_notification_id=notification_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
