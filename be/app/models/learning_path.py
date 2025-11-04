from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime


class LearningPath(Base):
    __tablename__ = 'learning_paths'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)  # Optional team ownership
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_days = Column(Integer, nullable=False)
    preferences_id = Column(Integer, ForeignKey("preferences.id"), nullable=True)

    # Metadata fields
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="owned_learning_paths")
    team = relationship("Team", back_populates="learning_paths")
    modules = relationship("Module", back_populates="learning_path", cascade="all, delete-orphan")
    preferences = relationship("Preferences", back_populates="learning_paths")
    progress_records = relationship("Progress", back_populates="learning_path", cascade="all, delete-orphan")

    def __init__(self, user_id, title, description, estimated_days, preferences_id=None, team_id=None, is_public=False):
        self.user_id = user_id
        self.team_id = team_id
        self.title = title
        self.description = description
        self.estimated_days = estimated_days
        self.preferences_id = preferences_id
        self.is_public = is_public
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def get_user_progress(self, user_id: str) -> float:
        """Get completion percentage for a specific user"""
        progress_record = next((p for p in self.progress_records if p.user_id == user_id), None)
        return progress_record.completion_percentage if progress_record else 0.0

    def is_completed_by_user(self, user_id: str) -> bool:
        """Check if this learning path is completed by a specific user"""
        progress_record = next((p for p in self.progress_records if p.user_id == user_id), None)
        return progress_record.is_completed if progress_record else False

    def get_all_user_progress(self) -> dict:
        """Get progress for all users who have started this learning path"""
        return {
            progress.user_id: {
                'completion_percentage': progress.completion_percentage,
                'is_completed': progress.is_completed,
                'started_at': progress.started_at,
                'completed_at': progress.completed_at
            }
            for progress in self.progress_records
        }

    def can_be_accessed_by_user(self, user_id: str) -> bool:
        """Check if a user can access this learning path"""
        # User can always access their own paths
        if self.user_id == user_id:
            return True

        # Public paths can be accessed by anyone
        if self.is_public:
            return True

        # Team members can access team paths
        if self.team_id:
            # This would need to be checked against team membership
            # For now, return True if team_id is set
            return True

        return False

    def create_copy_for_user(self, new_user_id: str, new_title: str = None) -> 'LearningPath':
        """Create a copy of this learning path for another user"""
        new_learning_path = LearningPath(
            user_id=new_user_id,
            title=new_title or f"Copy of {self.title}",
            description=self.description,
            estimated_days=self.estimated_days,
            preferences_id=self.preferences_id,
            is_public=False  # Copies are private by default
        )
        return new_learning_path

    @property
    def total_modules(self) -> int:
        """Get total number of modules in this learning path"""
        return len(self.modules)

    @property
    def total_users_started(self) -> int:
        """Get number of users who have started this learning path"""
        return len([p for p in self.progress_records if p.is_started])

    @property
    def total_users_completed(self) -> int:
        """Get number of users who have completed this learning path"""
        return len([p for p in self.progress_records if p.is_completed])

    @property
    def average_completion_percentage(self) -> float:
        """Get average completion percentage across all users"""
        if not self.progress_records:
            return 0.0
        total_completion = sum(p.completion_percentage for p in self.progress_records)
        return total_completion / len(self.progress_records)

    def __repr__(self):
        return f'<LearningPath: id={self.id}, title={self.title}, user_id={self.user_id}, modules={self.total_modules}>'
