"""
Notification Service

This module provides business logic for notification operations.
All methods use repository pattern for data access abstraction.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.schemas.core_schemas.notification_schema import NotificationResponse
from app.repositories import notification_repository

logger = get_logger(__name__)


async def get_user_notifications(
    db: AsyncSession,
    user_id: str,
    include_read: bool = True,
    include_deleted: bool = False,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Get paginated notifications for a user.

    Args:
        db: Database session
        user_id: ID of the user
        include_read: Whether to include read notifications
        include_deleted: Whether to include deleted notifications
        page: Page number for pagination
        per_page: Number of notifications per page

    Returns:
        Dictionary with notifications list and pagination info
    """
    logger.info(f"Getting notifications for user {user_id}, page {page}, per_page {per_page}")

    try:
        # Calculate offset
        offset = (page - 1) * per_page

        # Get notifications with filters
        notifications_data = await notification_repository.get_user_notifications_paginated(
            db=db,
            user_id=user_id,
            include_read=include_read,
            include_deleted=include_deleted,
            offset=offset,
            limit=per_page
        )

        # Get total count for pagination
        total_count = await notification_repository.count_user_notifications(
            db=db,
            user_id=user_id,
            include_read=include_read,
            include_deleted=include_deleted
        )

        # Get unread count
        unread_count = await notification_repository.count_unread_notifications(db, user_id)

        # Calculate pagination info
        has_next = offset + per_page < total_count
        has_prev = page > 1

        result = {
            "notifications": notifications_data,
            "total": total_count,
            "unread_count": unread_count,
            "has_next": has_next,
            "has_prev": has_prev
        }

        logger.info(f"Retrieved {len(notifications_data)} notifications for user {user_id}, "
                   f"total: {total_count}, unread: {unread_count}")

        return result

    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
        raise


async def get_unread_notification_count(db: AsyncSession, user_id: str) -> int:
    """
    Get count of unread notifications for a user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Number of unread notifications
    """
    logger.debug(f"Getting unread count for user {user_id}")

    try:
        count = await notification_repository.count_unread_notifications(db, user_id)
        logger.debug(f"User {user_id} has {count} unread notifications")
        return count

    except Exception as e:
        logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
        raise


async def get_notification_by_id(db: AsyncSession, notification_id: int, user_id: str) -> Optional[NotificationResponse]:
    """
    Get a specific notification by ID.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user (for ownership verification)

    Returns:
        NotificationResponse object or None if not found/no access
    """
    logger.info(f"Getting notification {notification_id} for user {user_id}")

    try:
        notification = await notification_repository.get_by_id_for_user(db, notification_id, user_id)

        if not notification:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return None

        logger.info(f"Successfully retrieved notification {notification_id}")
        return notification

    except Exception as e:
        logger.error(f"Error getting notification {notification_id} for user {user_id}: {str(e)}")
        raise


async def update_notification(db: AsyncSession, notification_id: int, user_id: str) -> Optional[NotificationResponse]:
    """
    Update notification (mark as read/deleted).
    Note: Request body parsing should be handled in the endpoint.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user (for ownership verification)

    Returns:
        Updated NotificationResponse object or None if not found
    """
    logger.info(f"Updating notification {notification_id} for user {user_id}")

    try:
        # Verify notification exists and belongs to user
        notification = await notification_repository.get_by_id_for_user(db, notification_id, user_id)

        if not notification:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return None

        # Update notification (repository handles the actual update fields)
        updated_notification = await notification_repository.update_notification(db, notification_id, user_id)

        logger.info(f"Successfully updated notification {notification_id}")
        return updated_notification

    except Exception as e:
        logger.error(f"Error updating notification {notification_id} for user {user_id}: {str(e)}")
        raise


async def mark_all_notifications_as_read(db: AsyncSession, user_id: str) -> int:
    """
    Mark all notifications as read for a user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Number of notifications marked as read
    """
    logger.info(f"Marking all notifications as read for user {user_id}")

    try:
        marked_count = await notification_repository.mark_all_as_read(db, user_id)
        logger.info(f"Marked {marked_count} notifications as read for user {user_id}")
        return marked_count

    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
        raise


async def delete_notification(db: AsyncSession, notification_id: int, user_id: str) -> bool:
    """
    Delete (soft delete) a notification.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user (for ownership verification)

    Returns:
        True if deletion successful, False if notification not found
    """
    logger.info(f"Deleting notification {notification_id} for user {user_id}")

    try:
        # Verify notification exists and belongs to user
        if not await notification_repository.get_by_id_for_user(db, notification_id, user_id):
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return False

        # Soft delete notification
        success = await notification_repository.soft_delete(db, notification_id, user_id)

        if success:
            logger.info(f"Successfully deleted notification {notification_id}")
        else:
            logger.warning(f"Failed to delete notification {notification_id}")

        return success

    except Exception as e:
        logger.error(f"Error deleting notification {notification_id} for user {user_id}: {str(e)}")
        raise
