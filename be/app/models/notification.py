from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from enum import Enum
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


class Notification(Base):
    """Notification model for user notifications"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # NotificationType enum values
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entity IDs for navigation/context
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    module_id = Column(Integer, nullable=True)
    
    # Notification state
    is_read = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    learning_path = relationship("LearningPath", backref="notifications")
    team = relationship("Team", backref="notifications")
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now()
    
    def to_dict(self):
        """Convert notification to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "learning_path_id": self.learning_path_id,
            "team_id": self.team_id,
            "module_id": self.module_id,
            "is_read": self.is_read,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }
