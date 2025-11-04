"""
Module Generation Schema
This schema defines the structure for validating responses from an AI model
when generating educational modules. It ensures that the generated content
contains all necessary metadata and adheres to specified constraints.
"""

from typing import List
from pydantic import BaseModel, Field


class ModuleResponse(BaseModel):
    """
    Pydantic model for validating LLM module generation responses.

    This ensures the AI response contains all required module metadata.
    """

    module_title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Clear, engaging title for the module"
    )

    module_description: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Comprehensive description of what learners will achieve in this module"
    )

    learning_objectives: List[str] = Field(
        ...,
        min_items=2,
        max_items=5,
        description="Specific learning objectives for this module"
    )

    selected_content_index: int = Field(
        ...,
        ge=0,
        description="Index of the selected content item from the provided content pool"
    )