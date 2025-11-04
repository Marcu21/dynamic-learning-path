"""
Statistics Service

This module provides business logic for user statistics operations.
All methods use repository pattern for data access abstraction.
Handles comprehensive user analytics including streaks, completion stats,
community comparisons, and learning insights.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import get_logger
from app.schemas.core_schemas.statistics_schema import UserStatisticsResponse
from app.repositories import statistics_repository

logger = get_logger(__name__)


async def get_user_statistics(db: AsyncSession, user_id: str) -> Optional[UserStatisticsResponse]:
    """
    Get comprehensive user statistics for profile page using optimized queries.

    This method uses a single comprehensive database query instead of multiple
    separate queries to dramatically improve performance.

    Args:
        db: Database session
        user_id: ID of the user to get statistics for

    Returns:
        UserStatisticsResponse object or None if user not found

    Raises:
        Exception: If there's an error retrieving statistics
    """
    logger.info(f"Getting comprehensive statistics for user {user_id}")

    try:
        # Get ALL statistics in one optimized call
        stats_data = await statistics_repository.get_comprehensive_user_statistics(db, user_id)
        
        if not stats_data:
            logger.warning(f"User {user_id} not found")
            return None

        # Build response object from comprehensive data
        statistics_response = UserStatisticsResponse(
            user_id=user_id,
            # Streak fields
            streak_days=stats_data.get("streak_days", 0),
            user_created_at=stats_data.get("user_created_at"),
            # Content completion fields
            completed_learning_paths=stats_data.get("completed_learning_paths", 0),
            modules_completed=stats_data.get("modules_completed", 0),
            skill_points_earned=stats_data.get("skill_points_earned", 0),
            quizzes_completed=stats_data.get("quizzes_completed", 0),
            # Time comparison fields
            user_total_minutes=stats_data.get("user_total_minutes", 0),
            community_average_minutes=stats_data.get("community_average_minutes", 0),
            # Daily learning data
            learning_time_data=stats_data.get("learning_time_data", {}),
            # Platform time summary
            platform_time_summary=stats_data.get("platform_time_summary", {}),
            # Key insights
            top_percentile_time=stats_data.get("top_percentile_time", 0.0),
            community_impact=stats_data.get("community_impact", 0.0),
            content_coverage=stats_data.get("content_coverage", 0.0)
        )

        logger.info(f"Successfully compiled statistics for user {user_id}")
        return statistics_response

    except Exception as error:
        logger.error(f"Error getting statistics for user {user_id}: {str(error)}")
        raise error
