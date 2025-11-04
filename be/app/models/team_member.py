from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.database import Base
from app.models.enums import TeamMemberRole


class TeamMember(Base):
    __tablename__ = 'team_members'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    team_id = Column(String(36), ForeignKey('teams.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    role = Column(Enum(TeamMemberRole), default=TeamMemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.now)  # Changed to match your datetime style
    
    # Relationships - Note: Your User model already has team_memberships relationship
    team = relationship("Team", back_populates="members")
    user = relationship("User")  # Simple relationship without back_populates since User model is unchanged
    
    def __init__(self, team_id: str, user_id: str, role: TeamMemberRole = TeamMemberRole.MEMBER):
        self.team_id = team_id
        self.user_id = user_id
        self.role = role

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"
