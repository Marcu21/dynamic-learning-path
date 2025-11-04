from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.database import Base


class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    team_lead_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)  # Changed to match your datetime style
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # Changed to match your datetime style

    # Relationships - Note: Your User model already has led_teams relationship
    team_lead = relationship("User")  # Simple relationship without back_populates since User model is unchanged
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="team")  # Your LearningPath already has this
    join_codes = relationship("TeamJoinCode", back_populates="team", cascade="all, delete-orphan")
    
    def __init__(self, name: str, team_lead_id: str, description: str = None):
        self.name = name
        self.team_lead_id = team_lead_id
        self.description = description
    
    def get_active_members(self):
        """Get all active team members"""
        return [member for member in self.members if member.team.is_active]
    
    def is_user_member(self, user_id: str) -> bool:
        """Check if user is a member of this team"""
        return any(member.user_id == user_id for member in self.members)
    
    def is_user_team_lead(self, user_id: str) -> bool:
        """Check if user is the team lead"""
        return self.team_lead_id == user_id
    
    def get_member_role(self, user_id: str):
        """Get the role of a specific user in this team"""
        for member in self.members:
            if member.user_id == user_id:
                return member.role
        return None
    
    def get_team_progress_summary(self) -> dict:
        """Get progress summary for all team members across all team learning paths"""
        active_members = self.get_active_members()
        team_paths = [path for path in self.learning_paths if path.team_id == self.id]
        
        total_paths = len(team_paths)
        total_members = len(active_members)
        
        if total_paths == 0 or total_members == 0:
            return {
                'total_learning_paths': total_paths,
                'total_members': total_members,
                'average_completion_percentage': 0.0,
                'members_completed_all_paths': 0,
                'most_popular_path': None,
                'least_popular_path': None,
                'path_completion_stats': []
            }
        
        # Calculate basic stats using your existing LearningPath methods
        completion_data = []
        for path in team_paths:
            path_completion = {
                'path_id': path.id,
                'path_title': path.title,
                'total_modules': path.total_modules,  # Using your property
                'members_started': path.total_users_started,  # Using your property
                'members_completed': path.total_users_completed,  # Using your property
                'average_completion': path.average_completion_percentage  # Using your property
            }
            completion_data.append(path_completion)
        
        # Calculate overall average
        overall_avg = sum(p['average_completion'] for p in completion_data) / len(completion_data) if completion_data else 0.0
        
        return {
            'total_learning_paths': total_paths,
            'total_members': total_members,
            'average_completion_percentage': overall_avg,
            'members_completed_all_paths': 0,  # Would need more complex calculation
            'most_popular_path': max(completion_data, key=lambda x: x['members_started']) if completion_data else None,
            'least_popular_path': min(completion_data, key=lambda x: x['members_started']) if completion_data else None,
            'path_completion_stats': completion_data
        }

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name}, lead={self.team_lead_id})>"
