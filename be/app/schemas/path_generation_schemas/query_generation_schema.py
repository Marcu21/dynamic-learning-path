"""
Query Generation Schema
This schema defines the structure for validating responses from an AI model
when generating platform-specific queries for different difficulty levels.
"""

from typing import Dict

from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    """
    Pydantic model for validating LLM query generation responses.

    This ensures the AI response contains properly structured platform queries
    for each difficulty level.
    """

    platform_queries: Dict[str, Dict[str, str]] = Field(
        ...,
        description="Nested dictionary with difficulty levels as keys, platforms as sub-keys, and queries as values"
    )
