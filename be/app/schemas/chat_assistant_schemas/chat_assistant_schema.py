"""
Chat Assistant Schema
This module defines schemas for the chat assistant's context and user location.
It includes user locations, chat context types, and user context location details.
"""

from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class UserLocation(str, Enum):
    """User's current location in the application"""
    DASHBOARD = "dashboard"
    LEARNING_PATH = "learning_path"
    MODULE = "module"
    QUIZ = "quiz"
    QUIZ_ATTEMPT_ACTIVE = "quiz_attempt_active"
    REVIEW_ANSWERS = "review_answers"


class ChatContext(str, Enum):
    """Types of context the assistant can retrieve"""
    LEARNING_PATH = "learning_path"
    MODULE = "module"
    QUIZ = "quiz"
    USER_PROGRESS = "user_progress"
    GENERAL = "general"
    RESTRICTED = "restricted"


class UserContextLocation(BaseModel):
    """User's current context/location in the application"""
    location: UserLocation
    learning_path_id: Optional[int] = None
    module_id: Optional[int] = None
    quiz_id: Optional[int] = None
    quiz_attempt_id: Optional[int] = None
    team_id: Optional[str] = None

    def get_hierarchy_context(self) -> Dict[str, Optional[int]]:
        """Get the hierarchical context (learning path -> module -> quiz)"""
        return {
            "learning_path_id": self.learning_path_id,
            "module_id": self.module_id,
            "quiz_id": self.quiz_id,
            "quiz_attempt_id": self.quiz_attempt_id,
            "team_id": self.team_id
        }
