"""
Notification Repository

This module provides data access methods for notification operations.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, select, func
from datetime import datetime

from app.core.logger import get_logger
from app.models.notification import Notification
from app.schemas.core_schemas.notification_schema import NotificationResponse, NotificationType

logger = get_logger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    learning_path_id: Optional[int] = None,
    team_id: Optional[str] = None,
    module_id: Optional[int] = None
) -> "NotificationResponse":
    """
    Create a new notification.

    Args:
        db: Database session
        user_id: ID of the user to notify
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        learning_path_id: Optional learning path ID
        team_id: Optional team ID
        module_id: Optional module ID

    Returns:
        NotificationResponse object with created notification details
    """
    logger.info(f"Creating notification for user {user_id}: {title}")

    try:
        # Create notification instance
        notification = Notification(
            user_id=user_id,
            type=notification_type.value,
            title=title,
            message=message,
            learning_path_id=learning_path_id,
            team_id=team_id,
            module_id=module_id,
            is_read=False,
            is_deleted=False
        )

        db.add(notification)
        await db.flush()  # Get the notification ID
        await db.commit()

        # Build response object
        from app.schemas.core_schemas.notification_schema import NotificationResponse
        notification_response = NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            learning_path_id=notification.learning_path_id,
            team_id=notification.team_id,
            module_id=notification.module_id,
            is_read=notification.is_read,
            is_deleted=notification.is_deleted,
            created_at=notification.created_at,
            read_at=notification.read_at
        )

        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification_response

    except Exception as e:
        logger.error(f"Error creating notification for user {user_id}: {str(e)}")
        await db.rollback()
        raise

async def get_user_notifications_paginated(
    db: AsyncSession,
    user_id: str,
    include_read: bool = True,
    include_deleted: bool = False,
    offset: int = 0,
    limit: int = 20
) -> List[NotificationResponse]:
    """
    Get paginated notifications for a user.

    Args:
        db: Database session
        user_id: ID of the user
        include_read: Whether to include read notifications
        include_deleted: Whether to include deleted notifications
        offset: Pagination offset
        limit: Number of notifications to return

    Returns:
        List of NotificationResponse objects
    """
    logger.debug(f"Getting notifications for user {user_id}, offset {offset}, limit {limit}")

    try:
        query = select(Notification).filter(Notification.user_id == user_id)

        # Apply filters
        if not include_read:
            query = query.filter(Notification.is_read == False)

        if not include_deleted:
            query = query.filter(Notification.is_deleted == False)

        # Order by creation date (newest first) and apply pagination
        query = query.order_by(desc(Notification.created_at)).offset(offset).limit(limit)
        result = await db.execute(query)
        notifications = result.scalars().all()

        result = []
        for notification in notifications:
            result.append(NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type,
                title=notification.title,
                message=notification.message,
                learning_path_id=notification.learning_path_id,
                team_id=notification.team_id,
                module_id=notification.module_id,
                is_read=notification.is_read,
                is_deleted=notification.is_deleted,
                created_at=notification.created_at,
                read_at=notification.read_at
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
        raise


async def count_user_notifications(
    db: AsyncSession,
    user_id: str,
    include_read: bool = True,
    include_deleted: bool = False
) -> int:
    """
    Count total notifications for a user.

    Args:
        db: Database session
        user_id: ID of the user
        include_read: Whether to include read notifications
        include_deleted: Whether to include deleted notifications

    Returns:
        Total count of notifications
    """
    logger.debug(f"Counting notifications for user {user_id}")

    try:
        query = select(func.count(Notification.id)).filter(Notification.user_id == user_id)

        # Apply filters
        if not include_read:
            query = query.filter(Notification.is_read == False)

        if not include_deleted:
            query = query.filter(Notification.is_deleted == False)

        result = await db.execute(query)
        return result.scalar()

    except Exception as e:
        logger.error(f"Error counting notifications for user {user_id}: {str(e)}")
        raise


async def count_unread_notifications(db: AsyncSession, user_id: str) -> int:
    """
    Count unread notifications for a user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Count of unread notifications
    """
    logger.debug(f"Counting unread notifications for user {user_id}")

    try:
        result = await db.execute(select(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False
            )
        ))
        count = result.scalar()

        return count

    except Exception as e:
        logger.error(f"Error counting unread notifications for user {user_id}: {str(e)}")
        raise


async def get_by_id_for_user(db: AsyncSession, notification_id: int, user_id: str) -> Optional[NotificationResponse]:
    """
    Get notification by ID for a specific user.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user (for ownership verification)

    Returns:
        NotificationResponse object or None if not found/no access
    """
    logger.debug(f"Getting notification {notification_id} for user {user_id}")

    try:
        result = await db.execute(select(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ))
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            learning_path_id=notification.learning_path_id,
            team_id=notification.team_id,
            module_id=notification.module_id,
            is_read=notification.is_read,
            is_deleted=notification.is_deleted,
            created_at=notification.created_at,
            read_at=notification.read_at
        )

    except Exception as e:
        logger.error(f"Error getting notification {notification_id} for user {user_id}: {str(e)}")
        raise


async def update_notification(db: AsyncSession, notification_id: int, user_id: str) -> Optional[NotificationResponse]:
    """
    Update notification (mark as read/deleted).
    Note: This is a simplified version - actual update fields should be passed as parameters.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user

    Returns:
        Updated NotificationResponse object or None if not found
    """
    logger.debug(f"Updating notification {notification_id} for user {user_id}")

    try:
        result = await db.execute(select(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ))
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        # Mark as read (simplified - should accept update parameters)
        notification.mark_as_read()
        await db.commit()

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            learning_path_id=notification.learning_path_id,
            team_id=notification.team_id,
            module_id=notification.module_id,
            is_read=notification.is_read,
            is_deleted=notification.is_deleted,
            created_at=notification.created_at,
            read_at=notification.read_at
        )

    except Exception as e:
        logger.error(f"Error updating notification {notification_id} for user {user_id}: {str(e)}")
        await db.rollback()
        raise


async def mark_all_as_read(db: AsyncSession, user_id: str) -> int:
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
        from sqlalchemy import update
        # Update all unread notifications
        stmt = update(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False
            )
        ).values(
            is_read=True,
            read_at=datetime.now()
        )

        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
        await db.rollback()
        raise


async def soft_delete(db: AsyncSession, notification_id: int, user_id: str) -> bool:
    """
    Soft delete a notification.

    Args:
        db: Database session
        notification_id: ID of the notification
        user_id: ID of the user (for ownership verification)

    Returns:
        True if deletion successful, False if notification not found
    """
    logger.info(f"Soft deleting notification {notification_id} for user {user_id}")

    try:
        result = await db.execute(select(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ))
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        notification.is_deleted = True
        await db.commit()

        return True

    except Exception as e:
        logger.error(f"Error soft deleting notification {notification_id} for user {user_id}: {str(e)}")
        await db.rollback()
        raise
