from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.database import Base


class TeamJoinCode(Base):
    __tablename__ = 'team_join_codes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(6), unique=True, nullable=False, index=True)
    team_id = Column(String(36), ForeignKey('teams.id'), nullable=False)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)  # Changed to match your datetime style
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    team = relationship("Team", back_populates="join_codes")
    creator = relationship("User")  # Simple relationship without back_populates
    
    def __init__(self, code: str, team_id: str, created_by: str, expires_at: datetime):
        self.code = code
        self.team_id = team_id
        self.created_by = created_by
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if the join code has expired"""
        return datetime.now() > self.expires_at  # Changed to match your datetime style
    
    def is_valid(self) -> bool:
        """Check if the join code is valid (active and not expired)"""
        return self.is_active and not self.is_expired()

    def __repr__(self):
        return f"<TeamJoinCode(code={self.code}, team_id={self.team_id}, active={self.is_active})>"
