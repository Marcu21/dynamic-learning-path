from sqlalchemy import Column, Integer, String, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import ExperienceLevel

class Preferences(Base):
    __tablename__ = 'preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    experience_level = Column(Enum(ExperienceLevel), nullable=False)
    learning_styles = Column(JSON, nullable=False)  # List of LearningStyle
    preferred_platforms = Column(JSON, nullable=False)  # List of strings
    study_time_minutes = Column(Integer, nullable=False)
    goals = Column(Text, nullable=False)

    learning_paths = relationship("LearningPath", back_populates="preferences")

    def __init__(self, subject, experience_level, learning_style, preferred_platforms, study_time, desired_goals):
        self.subject = subject
        self.experience_level = experience_level
        self.learning_styles = learning_style
        self.preferred_platforms = preferred_platforms
        self.study_time_minutes = study_time
        self.goals = desired_goals

    def __repr__(self):
        return f'<Preferences: id={self.id}, subject={self.subject}, experience={self.experience_level}, learning_style={self.learning_styles}, preferred_platforms={self.preferred_platforms}, study_time={self.study_time_minutes}, desired_goals={self.goals}>'
