from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.database import Base


class Progress(Base):
    """Tracks overall progress for a user on a specific learning path"""
    __tablename__ = 'progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    completion_percentage = Column(Float, default=0.0, nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Ensure one progress record per user per learning path
    __table_args__ = (UniqueConstraint('user_id', 'learning_path_id', name='unique_user_learning_path_progress'),)

    # Relationships
    user = relationship("User", back_populates="progress_records")
    learning_path = relationship("LearningPath", back_populates="progress_records")

    def __init__(self, user_id: str, learning_path_id: int):
        self.user_id = user_id
        self.learning_path_id = learning_path_id
        self.completion_percentage = 0.0
        self.started_at = datetime.now()
        self.last_updated_at = datetime.now()

    @property
    def is_completed(self) -> bool:
        """Check if the learning path is completed"""
        return self.completion_percentage >= 100.0

    @property
    def is_started(self) -> bool:
        """Check if the learning path has been started"""
        return self.completion_percentage > 0.0 or self.started_at is not None

    def mark_completed(self):
        """Mark the learning path as completed"""
        self.completion_percentage = 100.0
        self.completed_at = datetime.now()
        self.last_updated_at = datetime.now()

    def mark_incomplete(self):
        """Mark the learning path as incomplete"""
        self.completion_percentage = 0.0
        self.completed_at = None
        self.last_updated_at = datetime.now()

    def update_progress(self, percentage: float):
        """Update progress percentage"""
        self.completion_percentage = max(0.0, min(100.0, percentage))
        self.last_updated_at = datetime.now()

        if self.completion_percentage >= 100.0:
            self.mark_completed()

    @property
    def days_since_started(self) -> int:
        """Calculate days since learning path was started"""
        if not self.started_at:
            return 0
        return (datetime.now() - self.started_at).days

    @property
    def days_since_completed(self) -> int:
        """Calculate days since learning path was completed"""
        if not self.completed_at:
            return 0
        return (datetime.now() - self.completed_at).days

    def __repr__(self):
        return f'<Progress: user_id={self.user_id}, learning_path_id={self.learning_path_id}, completion={self.completion_percentage}%>'


class ModuleProgress(Base):
    """Tracks progress for a user on a specific module"""
    __tablename__ = 'module_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, default=func.now(), nullable=False)
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    attempts_count = Column(Integer, default=0, nullable=False)

    # Ensure one progress record per user per module
    __table_args__ = (UniqueConstraint('user_id', 'module_id', name='unique_user_module_progress'),)

    # Relationships
    user = relationship("User", back_populates="module_progress_records")
    module = relationship("Module", back_populates="progress_records")

    def __init__(self, user_id: str, module_id: int):
        self.user_id = user_id
        self.module_id = module_id
        self.is_completed = False
        self.time_spent_minutes = 0
        self.attempts_count = 0
        self.last_accessed_at = datetime.now()

    def mark_completed(self, time_spent: int = 0):
        """Mark the module as completed"""
        self.is_completed = True
        self.completed_at = datetime.now()
        self.last_accessed_at = datetime.now()
        if time_spent > 0:
            self.time_spent_minutes += time_spent

    def mark_incomplete(self):
        """Mark the module as incomplete"""
        self.is_completed = False
        self.completed_at = None
        self.last_accessed_at = datetime.now()

    def record_access(self, time_spent: int = 0):
        """Record that the module was accessed"""
        if not self.started_at:
            self.started_at = datetime.now()

        self.last_accessed_at = datetime.now()
        if time_spent > 0:
            self.time_spent_minutes += time_spent
        self.attempts_count += 1

    @property
    def days_since_started(self) -> int:
        """Calculate days since module was started"""
        if not self.started_at:
            return 0
        return (datetime.now() - self.started_at).days

    @property
    def days_since_completed(self) -> int:
        """Calculate days since module was completed"""
        if not self.completed_at:
            return 0
        return (datetime.now() - self.completed_at).days

    def __repr__(self):
        return f'<ModuleProgress: user_id={self.user_id}, module_id={self.module_id}, completed={self.is_completed}>'
