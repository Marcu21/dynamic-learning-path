"""
Path Blueprint Schema
This module defines the Pydantic schema for validating the response from an AI model
when generating a learning path blueprint. It ensures that the generated content
contains all necessary metadata and adheres to specified constraints.
"""

from typing import List, Dict
from pydantic import BaseModel, Field

from app.core.config import settings


class BlueprintResponse(BaseModel):
    """
    Pydantic model for validating LLM blueprint generation responses.

    This ensures the AI response contains all required fields in the correct format.
    """

    path_title: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Clear, engaging title for the learning path"
    )

    path_description: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Comprehensive description of what learners will achieve"
    )

    estimated_days: int = Field(
        ...,
        ge=1,
        le=365,
        description="Realistic completion timeline in days"
    )

    total_modules: int = Field(
        ...,
        ge=settings.min_number_of_modules,
        le=settings.max_number_of_modules,
        description="Optimal number of modules for the learning path"
    )

    module_difficulty_map: Dict[int, str] = Field(
        ...,
        description="Mapping of module order (1-based) to difficulty level"
    )

    learning_objectives: List[str] = Field(
        ...,
        min_items=2,
        max_items=5,
        description="High-level learning objectives for the entire path"
    )
