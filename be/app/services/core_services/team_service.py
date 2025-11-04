"""
Team Service

This module provides business logic for team operations.
All methods use repository pattern for data access abstraction.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets
import string

from app.core.logger import get_logger
from app.schemas.core_schemas.team_schema import (
    CurrentUserStatistics,
    LearningPathSummary,
    OverallProgress,
    PersonalTeamStatisticsApiResponse,
    ProgressSummary,
    TeamComparisonStatistics,
    TeamCreate,
    TeamDashboardApiResponse,
    TeamMember,
    TeamUpdate,
    TeamResponse,
    TeamMemberResponse,
    TeamMemberRoleEnum, TeamStats
)
from app.repositories import team_repository
from app.repositories import user_repository

logger = get_logger(__name__)


async def create_team(db: AsyncSession, team_data: TeamCreate, creator_id: str) -> TeamResponse:
    """
    Create a new team with the creator as team lead.

    Args:
        db: Database session
        team_data: Team creation data
        creator_id: ID of the user creating the team

    Returns:
        TeamResponse object with created team details
    """
    logger.info(f"Creating team '{team_data.name}' for user {creator_id}")

    try:
        # Ensure team lead is set to creator if not specified
        if not team_data.team_lead_id:
            team_data.team_lead_id = creator_id

        # Validate team name uniqueness
        if await team_repository.name_exists(db, team_data.name):
            logger.warning(f"Team name '{team_data.name}' already exists")
            raise ValueError("Team name already exists")

        # Create team
        team = await team_repository.create(db, team_data)

        # Add creator as team lead member
        await team_repository.add_member(db, team.id, creator_id, TeamMemberRoleEnum.TEAM_LEAD)

        # Get complete team with members
        complete_team = await team_repository.get_by_id_with_members(db, team.id)

        logger.info(f"Successfully created team {team.id}: '{team.name}'")
        return complete_team

    except Exception as e:
        logger.error(f"Error creating team '{team_data.name}': {str(e)}")
        raise


async def get_user_teams(db: AsyncSession, user_id: str) -> List[TeamResponse]:
    """
    Get all teams the user is a member of.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of TeamResponse objects
    """
    logger.info(f"Getting teams for user {user_id}")

    try:
        teams = await team_repository.get_user_teams(db, user_id)
        logger.info(f"Retrieved {len(teams)} teams for user {user_id}")
        return teams

    except Exception as e:
        logger.error(f"Error getting teams for user {user_id}: {str(e)}")
        raise


async def get_team_by_id(db: AsyncSession, team_id: str) -> Optional[TeamResponse]:
    """
    Get team by ID with all members.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        TeamResponse object or None if not found
    """
    logger.info(f"Getting team {team_id}")

    try:
        team = await team_repository.get_by_id_with_members(db, team_id)

        if not team:
            logger.warning(f"Team {team_id} not found")
            return None

        logger.info(f"Successfully retrieved team {team_id}: '{team.name}' with {len(team.members)} members")
        return team

    except Exception as e:
        logger.error(f"Error getting team {team_id}: {str(e)}")
        raise


async def update_team(db: AsyncSession, team_id: str, team_data: TeamUpdate) -> Optional[TeamResponse]:
    """
    Update team details.

    Args:
        db: Database session
        team_id: ID of the team to update
        team_data: Updated team data

    Returns:
        Updated TeamResponse object or None if not found
    """
    logger.info(f"Updating team {team_id}")

    try:
        # Validate team name uniqueness if name is being changed
        if team_data.name and await team_repository.name_exists_excluding_id(db, team_data.name, team_id):
            logger.warning(f"Team name '{team_data.name}' already exists")
            raise ValueError("Team name already exists")

        updated_team = await team_repository.update(db, team_id, team_data)

        if not updated_team:
            logger.warning(f"Team {team_id} not found for update")
            return None

        logger.info(f"Successfully updated team {team_id}")
        return updated_team

    except Exception as e:
        logger.error(f"Error updating team {team_id}: {str(e)}")
        raise


async def delete_team(db: AsyncSession, team_id: str) -> Dict[str, Any]:
    """
    Delete a team and all associated data.

    Args:
        db: Database session
        team_id: ID of the team to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting team {team_id}")

    try:
        deletion_result = await team_repository.delete_with_cascade(db, team_id)

        logger.info(f"Successfully deleted team {team_id}. "
                   f"Affected {deletion_result['affected_learning_paths_count']} learning paths, "
                   f"{deletion_result['affected_members_count']} members")

        return deletion_result

    except Exception as e:
        logger.error(f"Error deleting team {team_id}: {str(e)}")
        raise


async def user_has_team_access(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    Check if user has access to a team (is a member).

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        True if user has access, False otherwise
    """
    logger.debug(f"Checking team access for user {user_id} to team {team_id}")

    try:
        has_access = await team_repository.user_is_member(db, team_id, user_id)
        logger.debug(f"User {user_id} access to team {team_id}: {has_access}")
        return has_access

    except Exception as e:
        logger.error(f"Error checking team access for user {user_id} to team {team_id}: {str(e)}")
        return False


async def user_is_team_lead(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    Check if user is team lead of a specific team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        True if user is team lead, False otherwise
    """
    logger.debug(f"Checking team lead status for user {user_id} in team {team_id}")

    try:
        is_team_lead = await team_repository.user_is_team_lead(db, team_id, user_id)
        logger.debug(f"User {user_id} is team lead of team {team_id}: {is_team_lead}")
        return is_team_lead

    except Exception as e:
        logger.error(f"Error checking team lead status for user {user_id} in team {team_id}: {str(e)}")
        return False


async def generate_join_code(db: AsyncSession, team_id: str, expires_in_hours: int, created_by: str) -> Dict[str, Any]:
    """
    Generate a join code for a team.

    Args:
        db: Database session
        team_id: ID of the team
        expires_in_hours: Number of hours until expiration
        created_by: ID of the user creating the join code

    Returns:
        Dictionary with join code and expiration details
    """
    logger.info(f"Generating join code for team {team_id}, expires in {expires_in_hours} hours")

    try:
        # Generate secure random join code
        join_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        # Save join code
        join_code_data = await team_repository.create_join_code(db, team_id, join_code, expires_at, created_by)

        logger.info(f"Generated join code for team {team_id}: {join_code} (expires {expires_at})")
        return join_code_data

    except Exception as e:
        logger.error(f"Error generating join code for team {team_id}: {str(e)}")
        raise


async def join_team_by_code(db: AsyncSession, join_code: str, user_id: str) -> Optional[TeamMemberResponse]:
    """
    Join a team using a join code.

    Args:
        db: Database session
        join_code: The join code to use
        user_id: ID of the user joining

    Returns:
        TeamMemberResponse object or None if invalid code
    """
    logger.info(f"User {user_id} attempting to join team with code {join_code}")

    try:
        # Validate join code and get team
        team_id = await team_repository.validate_join_code(db, join_code)

        if not team_id:
            logger.warning(f"Invalid or expired join code: {join_code}")
            return None

        # Check if user is already a member
        if await team_repository.user_is_member(db, team_id, user_id):
            logger.warning(f"User {user_id} is already a member of team {team_id}")
            raise ValueError("User is already a member of this team")

        # Add user as team member
        team_member = await team_repository.add_member(db, team_id, user_id, TeamMemberRoleEnum.MEMBER)

        # Mark join code as used
        await team_repository.mark_join_code_used(db, join_code)

        logger.info(f"User {user_id} successfully joined team {team_id}")
        return team_member

    except Exception as e:
        logger.error(f"Error joining team with code {join_code} for user {user_id}: {str(e)}")
        raise


async def get_team_members(db: AsyncSession, team_id: str) -> List[TeamMemberResponse]:
    """
    Get all members of a team.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        List of TeamMemberResponse objects
    """
    logger.info(f"Getting members for team {team_id}")

    try:
        members = await team_repository.get_team_members(db, team_id)
        logger.info(f"Retrieved {len(members)} members for team {team_id}")
        return members

    except Exception as e:
        logger.error(f"Error getting members for team {team_id}: {str(e)}")
        raise


async def remove_team_member(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    Remove a member from a team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user to remove

    Returns:
        True if removal successful, False if member not found
    """
    logger.info(f"Removing user {user_id} from team {team_id}")

    try:
        # Verify member exists
        if not await team_repository.user_is_member(db, team_id, user_id):
            logger.warning(f"User {user_id} is not a member of team {team_id}")
            return False

        # Remove member
        success = await team_repository.remove_member(db, team_id, user_id)

        if success:
            logger.info(f"Successfully removed user {user_id} from team {team_id}")
        else:
            logger.warning(f"Failed to remove user {user_id} from team {team_id}")

        return success

    except Exception as e:
        logger.error(f"Error removing user {user_id} from team {team_id}: {str(e)}")
        raise


async def update_member_role(db: AsyncSession, team_id: str, user_id: str, new_role: TeamMemberRoleEnum) -> Optional[TeamMemberResponse]:
    """
    Update the role of a team member.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user whose role to update
        new_role: New role for the member

    Returns:
        Updated TeamMemberResponse object or None if member not found
    """
    logger.info(f"Updating role for user {user_id} in team {team_id} to {new_role}")

    try:
        # Verify member exists
        if not await team_repository.user_is_member(db, team_id, user_id):
            logger.warning(f"User {user_id} is not a member of team {team_id}")
            return None

        # Update member role
        updated_member = await team_repository.update_member_role(db, team_id, user_id, new_role)

        if updated_member:
            logger.info(f"Successfully updated role for user {user_id} in team {team_id} to {new_role}")
        else:
            logger.warning(f"Failed to update role for user {user_id} in team {team_id}")

        return updated_member

    except Exception as e:
        logger.error(f"Error updating role for user {user_id} in team {team_id}: {str(e)}")
        raise


async def is_user_team_member(db: AsyncSession, user_id: str, team_id: str) -> Optional[bool]:
    """
    Check if a user is a member of a specific team.

    Args:
        db: Database session
        user_id: ID of the user
        team_id: ID of the team

    Returns:
        True if user is a member, False if not, None if error
    """
    logger.debug(f"Checking if user {user_id} is a member of team {team_id}")

    try:
        is_member = await team_repository.user_is_member(db, team_id, user_id)
        logger.debug(f"User {user_id} is member of team {team_id}: {is_member}")
        return is_member

    except Exception as e:
        logger.error(f"Error checking membership for user {user_id} in team {team_id}: {str(e)}")
        return None
    

async def get_personal_team_statistics(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> PersonalTeamStatisticsApiResponse:
    """
    Get personal team statistics for a regular team member.

    Returns the user's individual performance within the team context, including:
    - Personal learning time and progress within team learning paths
    - User's rank compared to other team members
    - Team averages for comparison
    - Platform time distribution for team-related learning

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user requesting personal statistics

    Returns:
        PersonalTeamStatisticsApiResponse with user stats and team comparison

    Raises:
        Exception: If there's an error retrieving statistics
    """
    logger.info(f"Getting personal team statistics for user {user_id} in team {team_id}")

    try:
        # Get user's team-specific learning time and progress
        user_team_stats = await team_repository.get_user_team_learning_statistics(
            db=db,
            team_id=team_id,
            user_id=user_id
        )

        if not user_team_stats:
            logger.warning(f"No team statistics found for user {user_id} in team {team_id}")
            raise Exception("User team statistics not found")

        # Get user's progress summary for team learning paths
        learning_path_progress = await team_repository.get_user_team_learning_path_progress(
            db=db,
            team_id=team_id,
            user_id=user_id
        )

        # Get user's platform time distribution for team learning
        platform_time_split = await team_repository.get_user_team_platform_time_split(
            db=db,
            team_id=team_id,
            user_id=user_id
        )

        # Get team comparison data (user's rank and team averages)
        team_comparison_data = await team_repository.get_team_member_comparison_statistics(
            db=db,
            team_id=team_id,
            user_id=user_id
        )

        # Get user full name
        user_info = await user_repository.get_by_id(db, user_id)
        if not user_info:
            raise Exception(f"User {user_id} not found")

        # Build current user statistics
        current_user_stats = CurrentUserStatistics(
            user_id=user_id,
            full_name=user_info.full_name,
            user_team_learning_time_minutes=user_team_stats["total_learning_time_minutes"],
            learning_path_progress_summary=ProgressSummary(
                completed={"count": learning_path_progress["completed_count"]},
                in_progress={"count": learning_path_progress["in_progress_count"]}
            ),
            platform_split_minutes=platform_time_split
        )

        # Build team comparison statistics
        team_comparison_stats = TeamComparisonStatistics(
            rank=team_comparison_data["user_rank"],
            total_members=team_comparison_data["total_members"],
            average_learning_time_minutes=team_comparison_data["team_average_minutes"]
        )

        # Build final response
        response = PersonalTeamStatisticsApiResponse(
            user_stats=current_user_stats,
            team_comparison_stats=team_comparison_stats
        )

        logger.info(f"Successfully retrieved personal team statistics for user {user_id} in team {team_id}")
        return response

    except Exception as e:
        logger.error(f"Error getting personal team statistics for user {user_id} in team {team_id}: {str(e)}")
        raise


async def get_team_dashboard_statistics(
        db: AsyncSession,
        team_id: str
) -> TeamDashboardApiResponse:
    """
    Get comprehensive team dashboard statistics for team leads.

    Returns complete team analytics including:
    - Overall team progress across all learning paths
    - Individual member progress and learning times
    - Detailed learning path completion statistics
    - Team-wide platform usage summary

    Args:
        db: Database session
        team_id: ID of the team to get dashboard statistics for

    Returns:
        TeamDashboardApiResponse with complete team dashboard data

    Raises:
        Exception: If there's an error retrieving team statistics
    """
    logger.info(f"Getting team dashboard statistics for team {team_id}")

    try:
        # Get overall team progress statistics
        overall_progress_data = await team_repository.get_team_overall_progress_statistics(
            db=db,
            team_id=team_id
        )

        # Get all team members with their individual statistics
        team_members_data = await team_repository.get_team_members_detailed_statistics(
            db=db,
            team_id=team_id
        )

        # Get team-wide platform usage summary
        platform_summary = await team_repository.get_team_platform_usage_summary(
            db=db,
            team_id=team_id
        )

        # Build overall progress statistics
        overall_progress = OverallProgress(
            overall_completion_percentage=overall_progress_data["completion_percentage"],
            completed_user_lp_assignments=overall_progress_data["completed_assignments"],
            in_progress_user_lp_assignments=overall_progress_data["in_progress_assignments"],
            unstarted_user_lp_assignments=overall_progress_data["unstarted_assignments"]
        )

        # Build team member list with detailed statistics
        member_list = []
        for member_data in team_members_data:
            # Build learning path summary for this member
            learning_path_summary = LearningPathSummary(
                completed={
                    "count": member_data["completed_paths_count"],
                    "paths": member_data["completed_paths_details"]
                },
                in_progress={
                    "count": member_data["in_progress_paths_count"],
                    "paths": member_data["in_progress_paths_details"]
                },
                unstarted={
                    "count": member_data["unstarted_paths_count"],
                    "paths": member_data["unstarted_paths_details"]
                }
            )

            # Build team member object
            team_member = TeamMember(
                user_id=member_data["user_id"],
                full_name=member_data["full_name"],
                team_learning_time_minutes=member_data["total_learning_time_minutes"],
                learning_path_progress_summary=learning_path_summary
            )

            member_list.append(team_member)

        # Build final dashboard response
        dashboard_response = TeamDashboardApiResponse(
            overall_progress=overall_progress,
            member_list=member_list,
            platform_summary=platform_summary
        )

        logger.info(f"Successfully retrieved team dashboard statistics for team {team_id}")
        return dashboard_response

    except Exception as e:
        logger.error(f"Error getting team dashboard statistics for team {team_id}: {str(e)}")
        raise


async def get_team_statistics(db: AsyncSession, team_id: str) -> TeamStats:
    """
    Get basic team statistics for dashboard display.

    Calculates essential team metrics including total paths, members, and
    module-based completion percentage across all team members.

    Args:
        db: Database session
        team_id: ID of the team to get statistics for

    Returns:
        TeamStats object with basic team metrics

    Raises:
        Exception: If there's an error retrieving team statistics
    """
    logger.info(f"Getting team statistics for team {team_id}")

    try:
        # Get total number of learning paths for this team
        total_paths = await team_repository.get_team_learning_paths_count(db, team_id)

        # Get total number of active team members
        total_members = await team_repository.get_team_members_count(db, team_id)

        # Get overall team progress using the same logic as completion percentage
        avg_progress_percentage = await team_repository.get_average_progress(db, team_id)

        logger.info(
            f"Team {team_id} statistics: {total_paths} paths, {total_members} members, {avg_progress_percentage:.1f}% avg progress")

        return TeamStats(
            total_paths=total_paths,
            total_members=total_members,
            avg_progress_percentage=avg_progress_percentage
        )

    except Exception as e:
        logger.error(f"Error getting team statistics for team {team_id}: {str(e)}")
        raise
