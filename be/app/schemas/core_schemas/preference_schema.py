from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.models.enums import ExperienceLevel, LearningStyle


class PreferencesCreate(BaseModel):
    subject: str
    experience_level: ExperienceLevel
    learning_styles: List[LearningStyle]
    preferred_platforms: List[str]
    study_time_minutes: int
    goals: str

class PreferencesResponse(BaseModel):
    """Schema for preferences response"""
    id: int = Field(..., description="Unique identifier for preferences")
    subject: str = Field(..., description="Learning subject")
    experience_level: ExperienceLevel = Field(..., description="Experience level")
    learning_styles: List[LearningStyle] = Field(..., description="Preferred learning styles")
    preferred_platforms: List[str] = Field(..., description="Preferred learning platforms")
    study_time_minutes: int = Field(..., description="Daily study time in minutes")
    goals: str = Field(..., description="Learning goals and objectives")

    @field_validator('learning_styles', mode='before')
    @classmethod
    def validate_learning_styles(cls, v):
        """Convert learning styles from database JSON to enum list"""
        if isinstance(v, list):
            # Handle case where v is already a list of strings or enum values
            result = []
            for item in v:
                if isinstance(item, str):
                    # Convert string to enum
                    try:
                        result.append(LearningStyle(item))
                    except ValueError:
                        # If the string doesn't match any enum value, skip it or use a default
                        continue
                elif isinstance(item, LearningStyle):
                    result.append(item)
            return result
        return v

    @field_validator('preferred_platforms', mode='before')
    @classmethod
    def validate_preferred_platforms(cls, v):
        """Ensure preferred_platforms is a list of strings"""
        if isinstance(v, list):
            return [str(item) for item in v]
        return v

    class Config:
        from_attributes = True
