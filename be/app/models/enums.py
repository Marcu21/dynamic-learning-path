from enum import Enum

# Enums
class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading-writing"

class DifficultyLevel(Enum):
    """Enum for module difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class UserRole(str, Enum):
    """Enum for user roles"""
    USER = "user"
    TEAM_LEAD = "team_lead"

class TeamMemberRole(str, Enum):
    """Enum for team member roles"""
    MEMBER = "member"
    TEAM_LEAD = "team_lead"
