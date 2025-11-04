from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import DifficultyLevel


class Module(Base):
    """Module model representing individual learning modules within learning paths"""
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)
    content_url = Column(String(500), nullable=True)
    difficulty = Column(Enum(DifficultyLevel), nullable=True)
    learning_style = Column(JSON, nullable=True)
    learning_objectives = Column(JSON, nullable=True)
    created_at = Column(Integer, nullable=True, default=None)
    is_inserted = Column(Boolean, nullable=False, default=None)

    # Relationships
    learning_path = relationship("LearningPath", back_populates="modules")
    platform = relationship("Platform", back_populates="modules")
    quiz = relationship("Quiz", back_populates="module", uselist=False, cascade="all, delete-orphan")
    progress_records = relationship("ModuleProgress", back_populates="module", cascade="all, delete-orphan")

    def __init__(self, learning_path_id: int, platform_id: int, title: str, description: str,
                 duration: int, order_index: int, content_url: str = None,
                 difficulty: DifficultyLevel = None, learning_style: list = None,
                 learning_objectives: list = None, is_inserted: bool = False):
        """Initialize a new module"""
        self.learning_path_id = learning_path_id
        self.platform_id = platform_id
        self.title = title
        self.description = description
        self.duration = duration
        self.order_index = order_index
        self.content_url = content_url
        self.difficulty = difficulty
        self.learning_style = learning_style if isinstance(learning_style, list) else [
            learning_style] if learning_style else None
        self.learning_objectives = learning_objectives
        self.is_inserted = is_inserted

    def is_completed_by_user(self, user_id: str) -> bool:
        """Check if this module is completed by a specific user"""
        progress_record = next((p for p in self.progress_records if p.user_id == user_id), None)
        return progress_record.is_completed if progress_record else False

    def get_user_progress(self, user_id: str):
        """Get progress record for a specific user"""
        return next((p for p in self.progress_records if p.user_id == user_id), None)

    def get_completion_stats(self) -> dict:
        """Get completion statistics across all users"""
        total_users = len(self.progress_records)
        completed_users = len([p for p in self.progress_records if p.is_completed])

        return {
            'total_users': total_users,
            'completed_users': completed_users,
            'completion_rate': (completed_users / total_users * 100) if total_users > 0 else 0,
            'average_time_spent': sum(
                p.time_spent_minutes for p in self.progress_records) / total_users if total_users > 0 else 0
        }

    def get_users_completed(self) -> list:
        """Get list of user IDs who have completed this module"""
        return [p.user_id for p in self.progress_records if p.is_completed]

    def get_users_in_progress(self) -> list:
        """Get list of user IDs who have started but not completed this module"""
        return [p.user_id for p in self.progress_records if p.started_at and not p.is_completed]

    def mark_accessed_by_user(self, user_id: str, time_spent: int = 0):
        """Record that a user accessed this module"""
        progress_record = self.get_user_progress(user_id)
        if progress_record:
            progress_record.record_access(time_spent)
        else:
            # Create new progress record if it doesn't exist
            from app.models.progress import ModuleProgress
            new_progress = ModuleProgress(user_id=user_id, module_id=self.id)
            new_progress.record_access(time_spent)
            self.progress_records.append(new_progress)

    @property
    def has_quiz(self) -> bool:
        """Check if this module has an associated quiz"""
        return self.quiz is not None

    @property
    def estimated_hours(self) -> int:
        """Get estimated duration in minutes"""
        return self.duration if self.duration else 0

    @property
    def total_users_started(self) -> int:
        """Get number of users who have started this module"""
        return len([p for p in self.progress_records if p.started_at])

    @property
    def total_users_completed(self) -> int:
        """Get number of users who have completed this module"""
        return len([p for p in self.progress_records if p.is_completed])

    @property
    def completion_rate(self) -> float:
        """Get completion rate as percentage"""
        total = self.total_users_started
        if total == 0:
            return 0.0
        return (self.total_users_completed / total) * 100

    def __repr__(self):
        return f'<Module: id={self.id}, title={self.title}, learning_path_id={self.learning_path_id}, order_index={self.order_index}>'
