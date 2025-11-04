from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.database import Base
from app.models.enums import UserRole


class User(Base):
    """User model for managing user accounts and authentication"""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=False)  # Tracks login status
    skill_points = Column(Integer, default=0)  # Total skill points earned by the user

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    owned_learning_paths = relationship("LearningPath", back_populates="user", foreign_keys="LearningPath.user_id")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    module_progress_records = relationship("ModuleProgress", back_populates="user", cascade="all, delete-orphan")
    led_teams = relationship("Team", back_populates="team_lead", foreign_keys="Team.team_lead_id")
    team_memberships = relationship("TeamMember", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan",
                                 order_by="desc(Notification.created_at)")

    def __init__(self, username: str, email: str, full_name: str, role: UserRole = UserRole.USER):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role

    def get_learning_path_progress(self, learning_path_id: int):
        """Get progress for a specific learning path"""
        return next((p for p in self.progress_records if p.learning_path_id == learning_path_id), None)

    def get_module_progress(self, module_id: int):
        """Get progress for a specific module"""
        return next((p for p in self.module_progress_records if p.module_id == module_id), None)

    def get_accessible_learning_paths(self):
        """Get all learning paths this user can access (owned + team + public)"""
        accessible_paths = list(self.owned_learning_paths)

        # Add team learning paths
        for team_membership in self.team_memberships:
            if team_membership.team and team_membership.team.learning_paths:
                accessible_paths.extend(team_membership.team.learning_paths)

        # Remove duplicates by ID
        seen_ids = set()
        unique_paths = []
        for path in accessible_paths:
            if path.id not in seen_ids:
                seen_ids.add(path.id)
                unique_paths.append(path)

        return unique_paths

    def get_progress_summary(self) -> dict:
        """Get overall progress summary for this user"""
        total_paths = len(self.progress_records)
        completed_paths = len([p for p in self.progress_records if p.is_completed])
        in_progress_paths = len([p for p in self.progress_records if p.is_started and not p.is_completed])

        total_modules = len(self.module_progress_records)
        completed_modules = len([p for p in self.module_progress_records if p.is_completed])

        return {
            'total_learning_paths': total_paths,
            'completed_learning_paths': completed_paths,
            'in_progress_learning_paths': in_progress_paths,
            'not_started_learning_paths': total_paths - completed_paths - in_progress_paths,
            'total_modules': total_modules,
            'completed_modules': completed_modules,
            'overall_completion_percentage': (completed_modules / total_modules * 100) if total_modules > 0 else 0
        }

    def start_learning_path(self, learning_path_id: int):
        """Start a learning path (create progress record)"""
        existing_progress = self.get_learning_path_progress(learning_path_id)
        if not existing_progress:
            from app.models.progress import Progress
            new_progress = Progress(user_id=self.id, learning_path_id=learning_path_id)
            self.progress_records.append(new_progress)
            return new_progress
        return existing_progress

    def start_module(self, module_id: int):
        """Start a module (create module progress record)"""
        existing_progress = self.get_module_progress(module_id)
        if not existing_progress:
            from app.models.progress import ModuleProgress
            new_progress = ModuleProgress(user_id=self.id, module_id=module_id)
            self.module_progress_records.append(new_progress)
            return new_progress
        return existing_progress

    def get_teams(self):
        """Get all teams this user is a member of"""
        return [membership.team for membership in self.team_memberships if membership.team.is_active]

    def is_team_lead_of(self, team_id: str) -> bool:
        """Check if user is team lead of a specific team"""
        return any(team.id == team_id for team in self.led_teams if team.is_active)

    def is_member_of_team(self, team_id: str) -> bool:
        """Check if user is a member of a specific team"""
        return any(membership.team_id == team_id for membership in self.team_memberships if membership.team.is_active)

    def can_access_learning_path(self, learning_path) -> bool:
        """Check if user can access a specific learning path"""
        # User can always access their own paths
        if learning_path.user_id == self.id:
            return True

        # Public paths can be accessed by anyone
        if learning_path.is_public:
            return True

        # Team members can access team paths
        if learning_path.team_id and self.is_member_of_team(learning_path.team_id):
            return True

        return False

    @property
    def total_skill_points(self) -> int:
        """Calculate total skill points for this user"""
        module_points = len([p for p in self.module_progress_records if p.is_completed]) * 25
        quiz_points = len([attempt for attempt in self.quiz_attempts if attempt.skill_points_awarded]) * 30
        path_points = len([p for p in self.progress_records if p.is_completed]) * 50

        return module_points + quiz_points + path_points

    def __repr__(self):
        return f'<User: id={self.id}, username={self.username}, email={self.email}, role={self.role}>'
