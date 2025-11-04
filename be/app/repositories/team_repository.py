"""
Team Repository

This module provides data access methods for team operations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, case, func, select
import sqlalchemy
from sqlalchemy.orm import joinedload
from datetime import datetime

from app.core.logger import get_logger
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_join_code import TeamJoinCode
from app.models.user import User
from app.models.learning_path import LearningPath
from app.models.enums import TeamMemberRole
from app.schemas.core_schemas.team_schema import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberResponse,
    UserBasicInfo,
    TeamMemberRoleEnum
)
from app.models.module import Module
from app.models.platform import Platform
from app.models.progress import ModuleProgress, Progress

logger = get_logger(__name__)


async def create(db: AsyncSession, team_data: TeamCreate) -> TeamResponse:
    """
    Create a new team.

    Args:
        db: Database session
        team_data: Team creation data

    Returns:
        TeamResponse object
    """
    logger.info(f"Creating team: {team_data.name}")

    try:
        # Create team instance
        team = Team(
            name=team_data.name,
            team_lead_id=team_data.team_lead_id,
            description=team_data.description
        )

        db.add(team)
        await db.flush()  # Get the team ID
        await db.commit()

        logger.info(f"Created team {team.id}: {team.name}")
        return await _build_team_response(team, [])

    except Exception as e:
        logger.error(f"Error creating team {team_data.name}: {str(e)}")
        await db.rollback()
        raise


async def name_exists(db: AsyncSession, name: str) -> bool:
    """
    Check if team name already exists.

    Args:
        db: Database session
        name: Team name to check

    Returns:
        True if name exists, False otherwise
    """
    logger.debug(f"Checking if team name exists: {name}")

    try:
        result = await db.execute(select(Team).filter(Team.name == name))
        exists = result.scalar_one_or_none() is not None
        return exists

    except Exception as e:
        logger.error(f"Error checking team name existence for {name}: {str(e)}")
        return False


async def name_exists_excluding_id(db: AsyncSession, name: str, team_id: str) -> bool:
    """
    Check if team name exists excluding a specific team.

    Args:
        db: Database session
        name: Team name to check
        team_id: Team ID to exclude from check

    Returns:
        True if name exists, False otherwise
    """
    logger.debug(f"Checking if team name exists excluding {team_id}: {name}")

    try:
        result = await db.execute(select(Team).filter(
            and_(Team.name == name, Team.id != team_id)
        ))
        exists = result.scalar_one_or_none() is not None
        return exists

    except Exception as e:
        logger.error(f"Error checking team name existence for {name} excluding {team_id}: {str(e)}")
        return False


async def add_member(db: AsyncSession, team_id: str, user_id: str, role: TeamMemberRoleEnum) -> TeamMemberResponse:
    """
    Add a member to a team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user to add
        role: Role for the new member

    Returns:
        TeamMemberResponse object
    """
    logger.info(f"Adding user {user_id} to team {team_id} with role {role}")

    try:
        # Create team member
        team_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=TeamMemberRole.TEAM_LEAD if role == TeamMemberRoleEnum.TEAM_LEAD else TeamMemberRole.MEMBER
        )

        db.add(team_member)
        await db.commit()

        # Get user info for response
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        return TeamMemberResponse(
            id=team_member.id,
            user_id=team_member.user_id,
            team_id=team_member.team_id,
            role=TeamMemberRoleEnum.TEAM_LEAD if team_member.role == TeamMemberRole.TEAM_LEAD else TeamMemberRoleEnum.MEMBER,
            joined_at=team_member.joined_at,
            user=UserBasicInfo(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email
            ) if user else None
        )

    except Exception as e:
        logger.error(f"Error adding member {user_id} to team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def get_user_teams(db: AsyncSession, user_id: str) -> List[TeamResponse]:
    """
    Get all teams a user is a member of.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of TeamResponse objects
    """
    logger.debug(f"Getting teams for user: {user_id}")

    try:
        # Get teams where user is a member
        result = await db.execute(select(TeamMember).filter(TeamMember.user_id == user_id))
        team_members = result.scalars().all()

        result = []
        for team_member in team_members:
            team_result = await db.execute(select(Team).filter(Team.id == team_member.team_id))
            team = team_result.scalar_one_or_none()
            if team:
                members = await get_team_members(db, team.id)
                team_response = await _build_team_response(team, members)
                result.append(team_response)

        return result

    except Exception as e:
        logger.error(f"Error getting teams for user {user_id}: {str(e)}")
        raise


async def get_by_id_with_members(db: AsyncSession, team_id: str) -> Optional[TeamResponse]:
    """
    Get team by ID with all members.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        TeamResponse object or None if not found
    """
    logger.debug(f"Getting team by ID with members: {team_id}")

    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return None

        members = await get_team_members(db, team_id)
        return await _build_team_response(team, members)

    except Exception as e:
        logger.error(f"Error getting team {team_id} with members: {str(e)}")
        raise


async def update(db: AsyncSession, team_id: str, team_data: TeamUpdate) -> Optional[TeamResponse]:
    """
    Update team details.

    Args:
        db: Database session
        team_id: ID of the team to update
        team_data: Updated team data

    Returns:
        Updated TeamResponse object or None if not found
    """
    logger.info(f"Updating team: {team_id}")

    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return None

        # Update fields
        if team_data.name is not None:
            team.name = team_data.name
        if team_data.description is not None:
            team.description = team_data.description
        if team_data.team_lead_id is not None:
            team.team_lead_id = team_data.team_lead_id
        if team_data.is_active is not None:
            team.is_active = team_data.is_active

        team.updated_at = datetime.now()

        await db.commit()

        members = await get_team_members(db, team_id)
        return await _build_team_response(team, members)

    except Exception as e:
        logger.error(f"Error updating team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def delete_with_cascade(db: AsyncSession, team_id: str) -> Dict[str, Any]:
    """
    Delete team and all associated data.

    Args:
        db: Database session
        team_id: ID of the team to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting team {team_id} with cascade")

    try:
        # Get team first
        result = await db.execute(select(Team).options(
            joinedload(Team.members)
        ).filter(Team.id == team_id))
        team = result.unique().scalar_one_or_none()

        if not team:
            raise ValueError("Team not found")

        # Count affected data
        count_result = await db.execute(select(LearningPath).filter(LearningPath.team_id == team_id))
        affected_learning_paths_count = len(count_result.scalars().all())
        affected_members_count = len(team.members)

        # Delete the team (cascade will handle members, join codes, learning paths)
        await db.delete(team)
        await db.commit()

        return {
            "affected_learning_paths_count": affected_learning_paths_count,
            "affected_members_count": affected_members_count
        }

    except Exception as e:
        logger.error(f"Error deleting team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def user_is_member(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    Check if user is a member of a team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        True if user is a member, False otherwise
    """
    logger.debug(f"Checking if user {user_id} is member of team {team_id}")

    try:
        result = await db.execute(select(TeamMember).filter(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        ))
        member = result.scalar_one_or_none()

        return member is not None

    except Exception as e:
        logger.error(f"Error checking team membership for user {user_id}, team {team_id}: {str(e)}")
        return False


async def user_is_team_lead(db: AsyncSession, team_id: str, user_id: str) -> bool:
    """
    Check if user is team lead of a team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        True if user is team lead, False otherwise
    """
    logger.debug(f"Checking if user {user_id} is team lead of team {team_id}")

    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()
        return team.team_lead_id == user_id if team else False

    except Exception as e:
        logger.error(f"Error checking team lead status for user {user_id}, team {team_id}: {str(e)}")
        return False


async def create_join_code(db: AsyncSession, team_id: str, join_code: str, expires_at: datetime, created_by: str) -> Dict[str, Any]:
    """
    Create a join code for a team.

    Args:
        db: Database session
        team_id: ID of the team
        join_code: The join code string
        expires_at: When the code expires
        created_by: ID of the user creating the join code

    Returns:
        Dictionary with join code details
    """
    logger.info(f"Creating join code for team {team_id}")

    try:
        # Deactivate existing join codes for this team
        await db.execute(
             sqlalchemy.update(TeamJoinCode)
            .filter(TeamJoinCode.team_id == team_id)
            .values(is_active=False)
        )

        # Create new join code
        join_code_obj = TeamJoinCode(
            code=join_code,
            team_id=team_id,
            created_by=created_by,
            expires_at=expires_at
        )

        db.add(join_code_obj)
        await db.commit()

        return {
            "join_code": join_code,
            "expires_at": expires_at
        }

    except Exception as e:
        logger.error(f"Error creating join code for team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def validate_join_code(db: AsyncSession, join_code: str) -> Optional[str]:
    """
    Validate join code and return team ID if valid.

    Args:
        db: Database session
        join_code: The join code to validate

    Returns:
        Team ID if valid, None if invalid/expired
    """
    logger.debug(f"Validating join code: {join_code}")

    try:
        result = await db.execute(select(TeamJoinCode).filter(TeamJoinCode.code == join_code))
        join_code_obj = result.scalar_one_or_none()

        if not join_code_obj or not join_code_obj.is_valid():
            return None

        return join_code_obj.team_id

    except Exception as e:
        logger.error(f"Error validating join code {join_code}: {str(e)}")
        return None


async def mark_join_code_used(db: AsyncSession, join_code: str) -> None:
    """
    Mark join code as used (increment usage count).

    Args:
        db: Database session
        join_code: The join code to mark as used
    """
    logger.debug(f"Marking join code as used: {join_code}")

    try:
        result = await db.execute(select(TeamJoinCode).filter(TeamJoinCode.code == join_code))
        join_code_obj = result.scalar_one_or_none()

        if join_code_obj:
            join_code_obj.usage_count += 1
            await db.commit()

    except Exception as e:
        logger.error(f"Error marking join code as used {join_code}: {str(e)}")
        await db.rollback()


async def get_team_members(db: AsyncSession, team_id: str) -> List[TeamMemberResponse]:
    """
    Get all members of a team.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        List of TeamMemberResponse objects
    """
    logger.debug(f"Getting team members for team: {team_id}")

    try:
        result = await db.execute(
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .filter(TeamMember.team_id == team_id)
        )
        members = result.scalars().unique().all()

        result = []
        for member in members:
            user_info = None
            if member.user:
                user_info = UserBasicInfo(
                    id=member.user.id,
                    username=member.user.username,
                    full_name=member.user.full_name,
                    email=member.user.email
                )

            result.append(TeamMemberResponse(
                id=member.id,
                user_id=member.user_id,
                team_id=member.team_id,
                role=TeamMemberRoleEnum.TEAM_LEAD if member.role == TeamMemberRole.TEAM_LEAD else TeamMemberRoleEnum.MEMBER,
                joined_at=member.joined_at,
                user=user_info
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting team members for team {team_id}: {str(e)}")
        raise


async def remove_member(db: AsyncSession, team_id: str, user_id: str) -> bool:
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
        result = await db.execute(select(TeamMember).filter(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        ))
        member = result.scalar_one_or_none()

        if not member:
            return False

        await db.delete(member)
        await db.commit()

        return True

    except Exception as e:
        logger.error(f"Error removing member {user_id} from team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def update_member_role(db: AsyncSession, team_id: str, user_id: str, new_role: TeamMemberRoleEnum) -> Optional[TeamMemberResponse]:
    """
    Update the role of a team member.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user
        new_role: New role for the member

    Returns:
        Updated TeamMemberResponse object or None if member not found
    """
    logger.info(f"Updating role for user {user_id} in team {team_id} to {new_role}")

    try:
        result = await db.execute(
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .filter(and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            ))
        )
        member = result.scalars().unique().first()

        if not member:
            return None

        # Update role
        member.role = TeamMemberRole.TEAM_LEAD if new_role == TeamMemberRoleEnum.TEAM_LEAD else TeamMemberRole.MEMBER
        await db.commit()

        # Return updated member
        user_info = None
        if member.user:
            user_info = UserBasicInfo(
                id=member.user.id,
                username=member.user.username,
                full_name=member.user.full_name,
                email=member.user.email
            )

        return TeamMemberResponse(
            id=member.id,
            user_id=member.user_id,
            team_id=member.team_id,
            role=new_role,
            joined_at=member.joined_at,
            user=user_info
        )

    except Exception as e:
        logger.error(f"Error updating member role for user {user_id} in team {team_id}: {str(e)}")
        await db.rollback()
        raise


async def _build_team_response(team: Team, members: List[TeamMemberResponse]) -> TeamResponse:
    """
    Build TeamResponse object from Team model and members.

    Args:
        team: Team model instance
        members: List of team members

    Returns:
        TeamResponse object
    """
    try:
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            team_lead_id=team.team_lead_id,
            is_active=team.is_active,
            created_at=team.created_at,
            updated_at=team.updated_at,
            members=members,
            join_code=None  # Would need to get active join code if needed
        )

    except Exception as e:
        logger.error(f"Error building team response for team {team.id}: {str(e)}")
        raise


async def get_by_id(db: AsyncSession, team_id: str) -> Optional[TeamResponse]:
    """
    Get team by ID without members.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        TeamResponse object or None if not found
    """
    logger.debug(f"Getting team by ID: {team_id}")

    try:
        result = await db.execute(select(Team).filter(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return None

        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            team_lead_id=team.team_lead_id,
            is_active=team.is_active,
            created_at=team.created_at,
            updated_at=team.updated_at,
            members=[]  # No members loaded here
        )

    except Exception as e:
        logger.error(f"Error getting team {team_id}: {str(e)}")
        raise


async def get_user_team_learning_statistics(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> Dict[str, Any]:
    """
    Get user's learning statistics specific to team learning paths.

    Calculates total learning time spent on modules within team learning paths only.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        Dictionary with user's team-specific learning statistics
    """
    logger.debug(f"Getting team learning statistics for user {user_id} in team {team_id}")

    try:
        # Get user's total learning time on team learning paths
        time_result = await db.execute(select(
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('total_learning_time_minutes')
        ).select_from(ModuleProgress)
        .join(Module, ModuleProgress.module_id == Module.id)
        .join(LearningPath, Module.learning_path_id == LearningPath.id)
        .filter(
            and_(
                ModuleProgress.user_id == user_id,
                LearningPath.team_id == team_id
            )
        ))

        result = time_result.first()
        total_time = result.total_learning_time_minutes if result else 0

        logger.debug(f"User {user_id} has {total_time} minutes on team {team_id} learning paths")

        return {
            "total_learning_time_minutes": int(total_time)
        }

    except Exception as e:
        logger.error(f"Error getting team learning statistics for user {user_id} in team {team_id}: {str(e)}")
        raise


async def get_user_team_learning_path_progress(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> Dict[str, Any]:
    """
    Get user's progress summary on team learning paths.

    Counts completed and in-progress learning paths within the team.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        Dictionary with progress counts for team learning paths
    """
    logger.debug(f"Getting team learning path progress for user {user_id} in team {team_id}")

    try:
        # Get user's progress on team learning paths
        progress_result = await db.execute(select(
            func.count(
                case((Progress.completion_percentage >= 100.0, Progress.learning_path_id), else_=None)
            ).label('completed_count'),
            func.count(
                case(
                    (and_(Progress.completion_percentage > 0.0, Progress.completion_percentage < 100.0),
                     Progress.learning_path_id),
                    else_=None
                )
            ).label('in_progress_count')
        ).select_from(LearningPath)
                                           .outerjoin(Progress, and_(
            Progress.learning_path_id == LearningPath.id,
            Progress.user_id == user_id
        ))
                                           .filter(LearningPath.team_id == team_id))

        result = progress_result.first()

        completed_count = result.completed_count if result else 0
        in_progress_count = result.in_progress_count if result else 0

        logger.debug(f"User {user_id} has {completed_count} completed, {in_progress_count} in progress team paths")

        return {
            "completed_count": completed_count,
            "in_progress_count": in_progress_count
        }

    except Exception as e:
        logger.error(f"Error getting team learning path progress for user {user_id} in team {team_id}: {str(e)}")
        raise


async def get_user_team_platform_time_split(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> Dict[str, int]:
    """
    Get user's platform time distribution for team learning paths.

    Calculates time spent on each platform for modules within team learning paths.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        Dictionary mapping platform names to minutes spent
    """
    logger.debug(f"Getting platform time split for user {user_id} in team {team_id}")

    try:
        # Get platform time distribution for team learning paths
        platform_result = await db.execute(select(
            Platform.name.label('platform_name'),
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('total_minutes')
        ).select_from(ModuleProgress)
                                           .join(Module, ModuleProgress.module_id == Module.id)
                                           .join(Platform, Module.platform_id == Platform.id)
                                           .join(LearningPath, Module.learning_path_id == LearningPath.id)
                                           .filter(
            and_(
                ModuleProgress.user_id == user_id,
                LearningPath.team_id == team_id
            )
        )
                                           .group_by(Platform.name))

        platform_data = platform_result.all()

        platform_split = {}
        for row in platform_data:
            platform_split[row.platform_name] = int(row.total_minutes)

        logger.debug(f"User {user_id} platform split in team {team_id}: {platform_split}")

        return platform_split

    except Exception as e:
        logger.error(f"Error getting platform time split for user {user_id} in team {team_id}: {str(e)}")
        raise


async def get_team_member_comparison_statistics(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> Dict[str, Any]:
    """
    Get user's ranking and team comparison statistics.

    Calculates user's rank within team based on learning time and team averages.

    Args:
        db: Database session
        team_id: ID of the team
        user_id: ID of the user

    Returns:
        Dictionary with user's rank and team comparison data
    """
    logger.debug(f"Getting team comparison statistics for user {user_id} in team {team_id}")

    try:
        # Get all team members with their learning times
        members_time_result = await db.execute(select(
            TeamMember.user_id,
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('learning_time')
        ).select_from(TeamMember)
           .outerjoin(ModuleProgress, ModuleProgress.user_id == TeamMember.user_id)
           .outerjoin(Module, ModuleProgress.module_id == Module.id)
           .outerjoin(LearningPath, Module.learning_path_id == LearningPath.id)
           .filter(
            and_(
                TeamMember.team_id == team_id,
                LearningPath.team_id == team_id
            )
        )
        .group_by(TeamMember.user_id))

        member_times = members_time_result.all()

        # Calculate user's rank and team statistics
        user_time = 0
        all_times = []

        for member in member_times:
            time_spent = int(member.learning_time)
            all_times.append(time_spent)
            if member.user_id == user_id:
                user_time = time_spent

        # Sort times in descending order to get rank
        sorted_times = sorted(all_times, reverse=True)
        user_rank = sorted_times.index(user_time) + 1 if user_time in sorted_times else len(sorted_times)

        # Calculate team average
        team_average = int(sum(all_times) / len(all_times)) if all_times else 0
        total_members = len(member_times)

        logger.debug(f"User {user_id} rank: {user_rank}/{total_members}, average: {team_average} minutes")

        return {
            "user_rank": user_rank,
            "total_members": total_members,
            "team_average_minutes": team_average
        }

    except Exception as e:
        logger.error(f"Error getting team comparison statistics for user {user_id} in team {team_id}: {str(e)}")
        raise


async def get_team_overall_progress_statistics(
        db: AsyncSession,
        team_id: str
) -> Dict[str, Any]:
    """
    Get overall team progress statistics across all team learning paths.

    Calculates completion percentages and assignment counts for the entire team.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        Dictionary with team-wide progress statistics
    """
    logger.debug(f"Getting overall progress statistics for team {team_id}")

    try:
        # Get all team learning paths
        team_paths_result = await db.execute(select(
            LearningPath.id.label('path_id')
        ).where(LearningPath.team_id == team_id))

        team_paths = [row.path_id for row in team_paths_result.all()]

        if not team_paths:
            return {
                "completion_percentage": 0.0,
                "completed_assignments": 0,
                "in_progress_assignments": 0,
                "unstarted_assignments": 0
            }

        # Get all team members
        team_members_result = await db.execute(select(
            TeamMember.user_id
        ).where(TeamMember.team_id == team_id))

        team_members = [row.user_id for row in team_members_result.all()]

        if not team_members:
            return {
                "completion_percentage": 0.0,
                "completed_assignments": 0,
                "in_progress_assignments": 0,
                "unstarted_assignments": len(team_paths)
            }

        # Calculate module-based completion percentage
        total_modules_result = await db.execute(select(
            func.count(Module.id).label('total_modules')
        ).select_from(Module)
        .join(LearningPath, Module.learning_path_id == LearningPath.id)
        .where(LearningPath.team_id == team_id))

        total_modules = total_modules_result.scalar() or 0

        completed_modules_result = await db.execute(select(
            func.count(ModuleProgress.id).label('completed_modules')
        ).select_from(ModuleProgress)
        .join(Module, ModuleProgress.module_id == Module.id)
        .join(LearningPath, Module.learning_path_id == LearningPath.id)
        .where(
            and_(
                LearningPath.team_id == team_id,
                ModuleProgress.user_id.in_(team_members),
                ModuleProgress.is_completed
            )
        ))

        completed_modules = completed_modules_result.scalar() or 0

        # Calculate overall completion percentage based on modules
        completion_percentage = (
                    completed_modules / (total_modules * len(team_members)) * 100) if total_modules > 0 else 0.0

        # Analyze learning path assignments
        completed_assignments = 0
        in_progress_assignments = 0
        unstarted_assignments = 0

        for path_id in team_paths:
            # Get progress for this path from all team members
            path_progress_result = await db.execute(select(
                Progress.completion_percentage
            ).where(
                and_(
                    Progress.learning_path_id == path_id,
                    Progress.user_id.in_(team_members)
                )
            ))

            path_progress = [row.completion_percentage for row in path_progress_result.all() if
                             row.completion_percentage is not None]

            if not path_progress:
                # No progress from any member
                unstarted_assignments += 1
            elif all(progress >= 100.0 for progress in path_progress) and len(path_progress) == len(team_members):
                # All members completed this path
                completed_assignments += 1
            elif any(progress > 0.0 for progress in path_progress):
                # At least one member started this path
                in_progress_assignments += 1
            else:
                # No member started this path
                unstarted_assignments += 1

        logger.debug(
            f"Team {team_id} progress: {completed_assignments}/{len(team_paths)} completed, {completion_percentage:.1f}% average")

        return {
            "completion_percentage": round(completion_percentage, 1),
            "completed_assignments": completed_assignments,
            "in_progress_assignments": in_progress_assignments,
            "unstarted_assignments": unstarted_assignments
        }

    except Exception as e:
        logger.error(f"Error getting overall progress statistics for team {team_id}: {str(e)}")
        raise


async def get_team_members_detailed_statistics(
        db: AsyncSession,
        team_id: str
) -> List[Dict[str, Any]]:
    """
    Get detailed statistics for all team members.

    Returns comprehensive data for each team member including learning times,
    progress details, and learning path information.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        List of dictionaries with detailed member statistics
    """
    logger.debug(f"Getting detailed member statistics for team {team_id}")

    try:
        # Get team members with user information and learning times
        members_result = await db.execute(select(
            TeamMember.user_id,
            User.full_name,
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('total_learning_time')
        ).select_from(TeamMember)
          .join(User, TeamMember.user_id == User.id)
          .outerjoin(ModuleProgress, ModuleProgress.user_id == TeamMember.user_id)
          .outerjoin(Module, ModuleProgress.module_id == Module.id)
          .outerjoin(LearningPath, Module.learning_path_id == LearningPath.id)
          .filter(
            and_(
                TeamMember.team_id == team_id,
                LearningPath.team_id == team_id
            )
        )
          .group_by(TeamMember.user_id, User.full_name))

        members_data = members_result.all()

        detailed_statistics = []

        for member in members_data:
            user_id = member.user_id

            # Get detailed learning path progress for this member
            paths_progress_result = await db.execute(select(
                LearningPath.id,
                LearningPath.title,
                Progress.completion_percentage
            ).select_from(LearningPath)
             .outerjoin(Progress, and_(
                Progress.learning_path_id == LearningPath.id,
                Progress.user_id == user_id
            ))
            .filter(LearningPath.team_id == team_id))

            paths_data = paths_progress_result.all()

            # Categorize learning paths by completion status
            completed_paths = []
            in_progress_paths = []
            unstarted_paths = []

            for path in paths_data:
                path_details = {"id": str(path.id), "title": path.title}

                if path.completion_percentage is None:
                    unstarted_paths.append(path_details)
                elif path.completion_percentage >= 100.0:
                    completed_paths.append(path_details)
                else:
                    in_progress_paths.append(path_details)

            member_stats = {
                "user_id": user_id,
                "full_name": member.full_name,
                "total_learning_time_minutes": int(member.total_learning_time),
                "completed_paths_count": len(completed_paths),
                "completed_paths_details": completed_paths,
                "in_progress_paths_count": len(in_progress_paths),
                "in_progress_paths_details": in_progress_paths,
                "unstarted_paths_count": len(unstarted_paths),
                "unstarted_paths_details": unstarted_paths
            }

            detailed_statistics.append(member_stats)

        # Sort by learning time (descending)
        detailed_statistics.sort(key=lambda x: x["total_learning_time_minutes"], reverse=True)

        logger.debug(f"Retrieved detailed statistics for {len(detailed_statistics)} team members")

        return detailed_statistics

    except Exception as e:
        logger.error(f"Error getting detailed member statistics for team {team_id}: {str(e)}")
        raise


async def get_team_platform_usage_summary(
        db: AsyncSession,
        team_id: str
) -> Dict[str, int]:
    """
    Get team-wide platform usage summary.

    Aggregates total time spent across all platforms by all team members
    on team learning paths.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        Dictionary mapping platform names to total team minutes spent
    """
    logger.debug(f"Getting platform usage summary for team {team_id}")

    try:
        # Get team-wide platform usage
        platform_result = await db.execute(select(
            Platform.name.label('platform_name'),
            func.coalesce(func.sum(ModuleProgress.time_spent_minutes), 0).label('total_minutes')
        ).select_from(ModuleProgress)
           .join(Module, ModuleProgress.module_id == Module.id)
           .join(Platform, Module.platform_id == Platform.id)
           .join(LearningPath, Module.learning_path_id == LearningPath.id)
           .join(TeamMember, ModuleProgress.user_id == TeamMember.user_id)
           .filter(
            and_(
                LearningPath.team_id == team_id,
                TeamMember.team_id == team_id
            )
        )
                                           .group_by(Platform.name))

        platform_data = platform_result.all()

        platform_summary = {}
        for row in platform_data:
            platform_summary[row.platform_name] = int(row.total_minutes)

        logger.debug(f"Team {team_id} platform usage: {platform_summary}")

        return platform_summary

    except Exception as e:
        logger.error(f"Error getting platform usage summary for team {team_id}: {str(e)}")
        raise


async def get_team_learning_paths_count(db: AsyncSession, team_id: str) -> int:
    """
    Get the total number of learning paths for a team.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        Total count of learning paths for the team

    Raises:
        Exception: If there's an error counting learning paths
    """
    logger.debug(f"Getting learning paths count for team {team_id}")

    try:
        result = await db.execute(select(
            func.count(LearningPath.id)
        ).where(LearningPath.team_id == team_id))

        count = result.scalar() or 0

        logger.debug(f"Team {team_id} has {count} learning paths")
        return count

    except Exception as e:
        logger.error(f"Error getting learning paths count for team {team_id}: {str(e)}")
        raise


async def get_team_members_count(db: AsyncSession, team_id: str) -> int:
    """
    Get the total number of active team members.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        Total count of active team members

    Raises:
        Exception: If there's an error counting team members
    """
    logger.debug(f"Getting team members count for team {team_id}")

    try:
        result = await db.execute(select(
            func.count(TeamMember.id)
        ).where(TeamMember.team_id == team_id))

        count = result.scalar() or 0

        logger.debug(f"Team {team_id} has {count} members")
        return count

    except Exception as e:
        logger.error(f"Error getting team members count for team {team_id}: {str(e)}")
        raise


async def get_average_progress(db: AsyncSession, team_id: str) -> float:
    """
    Get average completion percentage based on module completion across all team members.

    Calculates the percentage of completed modules relative to total modules
    multiplied by team size (same logic as completion percentage from overall progress).

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        Average progress percentage (0.0 to 100.0)

    Raises:
        Exception: If there's an error calculating average progress
    """
    logger.debug(f"Getting average progress for team {team_id}")

    try:
        # Get team members count
        team_members_result = await db.execute(select(
            TeamMember.user_id
        ).where(TeamMember.team_id == team_id))

        team_members = [row.user_id for row in team_members_result.all()]

        if not team_members:
            logger.debug(f"Team {team_id} has no members, returning 0% progress")
            return 0.0

        # Get total modules count for team learning paths
        total_modules_result = await db.execute(select(
            func.count(Module.id)
        ).select_from(Module)
        .join(LearningPath, Module.learning_path_id == LearningPath.id)
        .where(LearningPath.team_id == team_id))

        total_modules = total_modules_result.scalar() or 0

        if total_modules == 0:
            logger.debug(f"Team {team_id} has no modules, returning 0% progress")
            return 0.0

        # Get completed modules count across all team members
        completed_modules_result = await db.execute(select(
            func.count(ModuleProgress.id)
        ).select_from(ModuleProgress)
        .join(Module, ModuleProgress.module_id == Module.id)
        .join(LearningPath, Module.learning_path_id == LearningPath.id)
        .where(
            and_(
                LearningPath.team_id == team_id,
                ModuleProgress.user_id.in_(team_members),
                ModuleProgress.is_completed
            )
        ))

        completed_modules = completed_modules_result.scalar() or 0

        # Calculate completion percentage: completed modules / (total modules * team size)
        total_expected_completions = total_modules * len(team_members)
        completion_percentage = (
                    completed_modules / total_expected_completions * 100) if total_expected_completions > 0 else 0.0

        logger.debug(
            f"Team {team_id} progress: {completed_modules}/{total_expected_completions} completions = {completion_percentage:.1f}%")

        return round(completion_percentage, 1)

    except Exception as e:
        logger.error(f"Error getting average progress for team {team_id}: {str(e)}")
        raise
