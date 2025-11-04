"""
Notification Schemas
"""
from enum import Enum

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class NotificationType(str, Enum):
    """Notification types for different events"""
    LEARNING_PATH_GENERATED = "learning_path_generated"
    TEAM_LEARNING_PATH_GENERATED = "team_learning_path_generated"
    LEARNING_PATH_COMPLETED = "learning_path_completed"
    MODULE_COMPLETED = "module_completed"
    TEAM_MEMBER_JOINED = "team_member_joined"
    TEAM_MEMBER_LEFT = "team_member_left"
    QUIZ_COMPLETED = "quiz_completed"


class NotificationUpdate(BaseModel):
    """Request model for updating notifications"""
    is_read: Optional[bool] = None
    is_deleted: Optional[bool] = None


class NotificationResponse(BaseModel):
    """Single notification response model"""
    id: int
    user_id: str
    type: str
    title: str
    message: str
    learning_path_id: Optional[int] = None
    team_id: Optional[str] = None
    module_id: Optional[int] = None
    is_read: bool
    is_deleted: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notifications list response"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UnreadCountResponse(BaseModel):
    """Unread notifications count response"""
    unread_count: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics response"""
    total_notifications: int
    unread_notifications: int
    read_notifications: int
    deleted_notifications: int
    notifications_by_type: Dict[str, int]


class NotificationUpdateResponse(BaseModel):
    """Response for notification updates (mark as read/deleted)"""
    success: bool
    message: str
    notification: NotificationResponse


class NotificationDeletionResponse(BaseModel):
    """Response for notification deletion"""
    success: bool
    message: str
    deleted_notification_id: int


class MarkAllReadResponse(BaseModel):
    """Response for marking all notifications as read"""
    success: bool
    message: str
    marked_count: int
