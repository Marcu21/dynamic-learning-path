"""
Statistics Repository

This module provides data access methods for user statistics operations.
Handles all database queries and aggregations for user analytics including
streaks, completion stats, community comparisons, and learning insights.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, distinct, case, select
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logger import get_logger
from app.models.user import User
from app.models.progress import Progress, ModuleProgress
from app.models.quiz import QuizAttempt
from app.models.learning_path import LearningPath
from app.models.module import Module
from app.models.platform import Platform

logger = get_logger(__name__)


async def get_comprehensive_user_statistics(db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get ALL user statistics in a single optimized query to improve performance.
    
    This replaces multiple separate queries with one comprehensive query that 
    fetches all needed statistics at once.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        Dictionary with all user statistics or None if user not found
    """
    logger.debug(f"Getting comprehensive statistics for user {user_id}")
    
    try:
        # Main comprehensive query that gets most statistics in one go
        main_stats_result = await db.execute(select(
            User.id.label('user_id'),
            User.created_at.label('user_created_at'),
            User.username,
            User.email,
            # Completion statistics
            func.count(distinct(Progress.learning_path_id)).label('completed_learning_paths'),
            func.count(distinct(case((ModuleProgress.is_completed == True, ModuleProgress.id), else_=None))).label('modules_completed'),
            func.count(distinct(QuizAttempt.id)).label('quizzes_completed'),
            # Time statistics
            func.sum(func.coalesce(ModuleProgress.time_spent_minutes, 0)).label('user_total_minutes'),
        ).select_from(User)
        .outerjoin(Progress, and_(Progress.user_id == User.id, Progress.completion_percentage >= 100.0))
        .outerjoin(ModuleProgress, ModuleProgress.user_id == User.id)
        .outerjoin(QuizAttempt, QuizAttempt.user_id == User.id)
        .filter(User.id == user_id)
        .group_by(User.id, User.created_at, User.username, User.email))
        
        main_stats_query = main_stats_result.first()
        
        if not main_stats_query:
            logger.warning(f"User {user_id} not found")
            return None
        
        # Convert to dictionary
        main_stats = {
            'user_id': main_stats_query.user_id,
            'user_created_at': main_stats_query.user_created_at.isoformat() if main_stats_query.user_created_at else None,
            'username': main_stats_query.username,
            'email': main_stats_query.email,
            'completed_learning_paths': main_stats_query.completed_learning_paths or 0,
            'modules_completed': main_stats_query.modules_completed or 0,
            'quizzes_completed': main_stats_query.quizzes_completed or 0,
            'user_total_minutes': float(main_stats_query.user_total_minutes or 0),
        }
        
        # Calculate skill points based on business logic:
        # - 25 points per completed module
        # - 30 points per quiz attempt 
        # - 50 points per completed learning path
        skill_points_earned = (
            (main_stats['modules_completed'] * settings.default_module_skill_points) +
            (main_stats['quizzes_completed'] * settings.default_quiz_skill_points) +
            (main_stats['completed_learning_paths'] * settings.default_path_skill_points)
        )
        main_stats['skill_points_earned'] = float(skill_points_earned)
        
        # Get community average in a single efficient query
        community_avg_subquery = select(
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('user_total')
        ).where(ModuleProgress.user_id == User.id).correlate(User).scalar_subquery()
        
        community_avg_result = await db.execute(select(
            func.avg(community_avg_subquery)
        ).where(User.is_active == True))
        community_avg = community_avg_result.scalar() or 0.0
        
        main_stats['community_average_minutes'] = float(community_avg)
        
        # Get streak data efficiently
        streak_data = await get_user_streak_data_optimized(db, user_id)
        main_stats.update(streak_data)
        
        # Get daily learning data efficiently  
        daily_learning_data = await get_daily_learning_time_data_optimized(db, user_id)
        main_stats['learning_time_data'] = daily_learning_data
        
        # Get platform time summary efficiently
        platform_time_data = await get_platform_time_summary_optimized(db, user_id)
        main_stats['platform_time_summary'] = platform_time_data
        
        # Get insights data efficiently
        insights_data = await get_user_insights_data_optimized(db, user_id, main_stats['user_total_minutes'])
        main_stats.update(insights_data)
        
        logger.info(f"Successfully retrieved comprehensive statistics for user {user_id}")
        return main_stats
        
    except Exception as e:
        logger.error(f"Error getting comprehensive statistics for user {user_id}: {str(e)}")
        raise


async def get_user_streak_data_optimized(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """
    Optimized streak calculation using SQLAlchemy expressions for PostgreSQL compatibility.
    """
    try:
        # Get all activity dates (module completions and quiz attempts) using SQLAlchemy  
        module_dates = select(
            func.date(ModuleProgress.completed_at).label('activity_date')
        ).where(
            and_(
                ModuleProgress.user_id == user_id,
                ModuleProgress.is_completed == True,
                ModuleProgress.completed_at.isnot(None)
            )
        ).distinct().subquery()

        quiz_dates = select(
            func.date(QuizAttempt.completed_at).label('activity_date')
        ).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.completed_at.isnot(None)
            )
        ).distinct().subquery()

        # Get unique dates from both sources
        module_activity_result = await db.execute(select(module_dates.c.activity_date))
        quiz_activity_result = await db.execute(select(quiz_dates.c.activity_date))
        
        module_activity = module_activity_result.all()
        quiz_activity = quiz_activity_result.all()
        
        # Combine dates and sort
        all_dates = set()
        for row in module_activity:
            all_dates.add(row.activity_date)
        for row in quiz_activity:
            all_dates.add(row.activity_date)
            
        activity_dates = sorted(list(all_dates), reverse=True)

        # Calculate current streak
        streak_days = 0
        current_date = datetime.now().date()

        if activity_dates:
            # Check if most recent activity was today or yesterday
            most_recent = activity_dates[0]
            days_since_recent = (current_date - most_recent).days
            
            if days_since_recent <= 1:  # Today or yesterday
                streak_days = 1
                prev_date = most_recent
                
                # Count consecutive days
                for activity_date in activity_dates[1:]:
                    days_diff = (prev_date - activity_date).days
                    if days_diff == 1:  # Consecutive day
                        streak_days += 1
                        prev_date = activity_date
                    else:
                        break  # Streak broken
        
        return {"streak_days": streak_days}
        
    except Exception as e:
        logger.error(f"Error calculating optimized streak for user {user_id}: {str(e)}")
        return {"streak_days": 0}


async def get_daily_learning_time_data_optimized(db: AsyncSession, user_id: str, days_back: int = 30) -> Dict[str, float]:
    """
    Optimized daily learning time data using a single query.
    """
    try:
        start_date = datetime.now().date() - timedelta(days=days_back)
        
        # Single query for daily time data
        daily_data_result = await db.execute(select(
            func.date(ModuleProgress.last_accessed_at).label('activity_date'),
            func.sum(ModuleProgress.time_spent_minutes).label('total_minutes')
        ).where(
            and_(
                ModuleProgress.user_id == user_id,
                ModuleProgress.last_accessed_at.isnot(None),
                func.date(ModuleProgress.last_accessed_at) >= start_date
            )
        ).group_by(func.date(ModuleProgress.last_accessed_at)))
        
        daily_data_query = daily_data_result.all()
        
        # Convert to dictionary
        daily_data = {}
        for row in daily_data_query:
            date_str = row.activity_date.strftime('%Y-%m-%d')
            daily_data[date_str] = float(row.total_minutes or 0)
        
        return daily_data
        
    except Exception as e:
        logger.error(f"Error getting optimized daily learning data for user {user_id}: {str(e)}")
        return {}


async def get_platform_time_summary_optimized(db: AsyncSession, user_id: str) -> Dict[str, float]:
    """
    Optimized platform time summary using joins instead of subqueries.
    """
    try:
        platform_time_result = await db.execute(select(
            Platform.name.label('platform_name'),
            func.sum(ModuleProgress.time_spent_minutes).label('total_time')
        ).select_from(ModuleProgress)
        .join(Module, Module.id == ModuleProgress.module_id)
        .join(Platform, Platform.id == Module.platform_id)
        .where(ModuleProgress.user_id == user_id)
        .group_by(Platform.name))

        platform_time_query = platform_time_result.all()

        # Calculate total minutes across all platforms
        platform_minutes = {}
        total_minutes = 0

        for row in platform_time_query:
            minutes = float(row.total_time or 0)
            platform_minutes[row.platform_name] = minutes
            total_minutes += minutes

        # Convert to percentages
        platform_data = {}
        if total_minutes > 0:
            for platform, minutes in platform_minutes.items():
                percentage = (minutes / total_minutes) * 100
                platform_data[platform] = round(percentage, 2)

        return platform_data

    except Exception as e:
        logger.error(f"Error getting optimized platform time summary for user {user_id}: {str(e)}")
        return {}


async def get_user_insights_data_optimized(db: AsyncSession, user_id: str, user_total_minutes: float) -> Dict[str, Any]:
    """
    Optimized insights calculation using SQLAlchemy for PostgreSQL compatibility.
    """
    try:
        # Get all user times for percentile calculation using SQLAlchemy
        user_times_result = await db.execute(select(
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('total_time')
        ).select_from(User)
                                             .outerjoin(ModuleProgress, ModuleProgress.user_id == User.id)
                                             .where(User.is_active == True)
                                             .group_by(User.id))

        user_times_query = user_times_result.all()

        user_times = [float(row.total_time) for row in user_times_query]
        total_users = len(user_times)
        total_community_time = sum(user_times)

        # Calculate percentile
        if total_users <= 1:
            percentile = 0.0
        else:
            users_below = sum(1 for time in user_times if time < user_total_minutes)
            percentile = 100.0 - (users_below / total_users) * 100.0

        # Ensure percentile is capped at 100%
        percentile = min(100.0, max(0.1, percentile))

        # Calculate community impact
        if total_community_time > 0:
            community_impact = (user_total_minutes / total_community_time) * 100.0
            community_impact = min(100.0, max(0.0, community_impact))
        else:
            community_impact = 0.0

        # Get content coverage efficiently
        content_coverage_result = await db.execute(select(
            func.count(distinct(LearningPath.id)).label('total_paths'),
            func.count(
                distinct(case((Progress.completion_percentage >= 100, Progress.learning_path_id), else_=None))).label(
                'completed_paths')
        )
           .select_from(LearningPath)
           .outerjoin(Progress,
                      and_(Progress.learning_path_id == LearningPath.id,
                           Progress.user_id == user_id))
           .where(LearningPath.user_id == user_id))

        content_coverage_query = content_coverage_result.first()

        total_paths = content_coverage_query.total_paths or 0
        completed_paths = content_coverage_query.completed_paths or 0
        content_coverage = (completed_paths / total_paths * 100) if total_paths > 0 else 0.0
        content_coverage = min(100.0, max(0.0, content_coverage))

        return {
            "top_percentile_time": round(percentile, 1),
            "community_impact": round(community_impact, 2),
            "content_coverage": round(content_coverage, 1)
        }

    except Exception as e:
        logger.error(f"Error getting optimized insights for user {user_id}: {str(e)}")
        return {
            "top_percentile_time": 0.0,
            "community_impact": 0.0,
            "content_coverage": 0.0
        }
