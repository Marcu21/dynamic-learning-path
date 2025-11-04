"""
Teams API Endpoints

This module provides FastAPI endpoints for team management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db_session
from app.schemas.core_schemas.team_schema import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberResponse,
    UpdateTeamMemberRequest,
    JoinTeamRequest,
    JoinCodeResponse,
    TeamDeletionResponse,
    RemoveMemberResponse, TeamStats
)
from app.services.core_services import team_service
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


# =============================
# BASIC TEAM MANAGEMENT
# =============================

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
        team_data: TeamCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new team
    """
    try:
        # Set team lead to current user if not specified
        if not team_data.team_lead_id:
            team_data.team_lead_id = current_user.id

        # Verify user can be team lead (only if different from current user)
        if team_data.team_lead_id != current_user.id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Only team leads can assign other team leads")

        team = await team_service.create_team(
            db=db,
            team_data=team_data,
            creator_id=current_user.id
        )

        return team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/my-teams", response_model=List[TeamResponse])
async def get_my_teams(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get all teams the current user is a member of
    """
    try:
        teams = await team_service.get_user_teams(
            db=db,
            user_id=current_user.id
        )

        return teams

    except Exception as e:
        logger.error(f"Error getting teams for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get team details by ID
    """
    try:
        # Verify user has access to team
        if not await team_service.user_has_team_access(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied to team")

        team = await team_service.get_team_by_id(
            db=db,
            team_id=team_id
        )

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        return team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
        team_data: TeamUpdate,
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Update team details (only team lead can update)
    """
    try:
        # Verify user is team lead of this team
        if not await team_service.user_is_team_lead(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Only team leads can update team")

        updated_team = await team_service.update_team(
            db=db,
            team_id=team_id,
            team_data=team_data
        )

        if not updated_team:
            raise HTTPException(status_code=404, detail="Team not found")

        return updated_team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{team_id}", response_model=TeamDeletionResponse)
async def delete_team(
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a team (only team lead can delete)
    """
    try:
        # Verify user is team lead of this team
        if not await team_service.user_is_team_lead(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Only team leads can delete team")

        deletion_result = await team_service.delete_team(
            db=db,
            team_id=team_id
        )

        return TeamDeletionResponse(
            success=True,
            message="Team deleted successfully",
            deleted_team_id=team_id,
            affected_learning_paths_count=deletion_result["affected_learning_paths_count"],
            affected_members_count=deletion_result["affected_members_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# JOIN CODE MANAGEMENT
# =============================

@router.post("/{team_id}/join-code", response_model=JoinCodeResponse)
async def generate_join_code(
        team_id: str = Path(..., description="Team ID"),
        expires_in_hours: int = Query(168, ge=1, le=720,
                                      description="Hours until code expires (default 7 days, max 30 days)"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a join code for a team
    """
    try:
        # Verify user is team lead of this team
        if not await team_service.user_is_team_lead(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Only team leads can generate join codes")

        join_code_data = await team_service.generate_join_code(
            db=db,
            team_id=team_id,
            expires_in_hours=expires_in_hours,
            created_by=current_user.id
        )

        return JoinCodeResponse(
            join_code=join_code_data["join_code"],
            expires_at=join_code_data["expires_at"],
            team_id=team_id,
            message="Join code generated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating join code for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/join", response_model=TeamMemberResponse)
async def join_team_by_code(
        join_data: JoinTeamRequest,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Join a team using a join code
    """
    try:
        team_member = await team_service.join_team_by_code(
            db=db,
            join_code=join_data.join_code,
            user_id=current_user.id
        )

        if not team_member:
            raise HTTPException(status_code=400, detail="Invalid or expired join code")

        return team_member

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining team with code {join_data.join_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# TEAM MEMBER MANAGEMENT
# =============================

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get all members of a team
    """
    try:
        # Verify user has access to team
        if not await team_service.user_has_team_access(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied to team")

        members = await team_service.get_team_members(
            db=db,
            team_id=team_id
        )

        return members

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team members for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{team_id}/members/{user_id}", response_model=RemoveMemberResponse)
async def remove_team_member(
        team_id: str = Path(..., description="Team ID"),
        user_id: str = Path(..., description="User ID to remove"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Remove a member from a team (only team lead can remove members)
    """
    try:
        # Verify user is team lead of this team
        if not await team_service.user_is_team_lead(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Only team leads can remove members")

        # Prevent team lead from removing themselves
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Team lead cannot remove themselves")

        success = await team_service.remove_team_member(
            db=db,
            team_id=team_id,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Team member not found")

        return RemoveMemberResponse(
            success=True,
            message="Team member removed successfully",
            removed_user_id=user_id,
            team_id=team_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member {user_id} from team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{team_id}/members/{user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
        role_data: UpdateTeamMemberRequest,
        team_id: str = Path(..., description="Team ID"),
        user_id: str = Path(..., description="User ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Update the role of a team member (only team lead can update roles)
    """
    try:
        # Verify user is team lead of this team
        if not await team_service.user_is_team_lead(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Only team leads can update member roles")

        # Prevent changing own role
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot change your own role")

        updated_member = await team_service.update_member_role(
            db=db,
            team_id=team_id,
            user_id=user_id,
            new_role=role_data.role
        )

        if not updated_member:
            raise HTTPException(status_code=404, detail="Team member not found")

        return updated_member

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role for member {user_id} in team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{team_id}/statistics", response_model=TeamStats)
async def get_team_statistics(
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive team statistics"""
    try:
        # Check if user has team access using async service method
        if not await team_service.user_has_team_access(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="You must be a team member to view team statistics"
            )

        return await team_service.get_team_statistics(
            db=db,
            team_id=team_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team statistics for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting team statistics: {str(e)}")


@router.get("/{team_id}/personal")
async def get_team_statistics_view(
        team_id: str = Path(..., description="Team ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get team statistics view - returns different data based on user role.

    For team members: Returns PersonalTeamStatisticsApiResponse with personal stats and team comparison
    For team leads: Returns TeamDashboardApiResponse with full team dashboard data

    This endpoint provides comprehensive team statistics tailored to the user's role and permissions.
    Team members see their personal performance within team context, while team leads get
    full visibility into all team member progress and detailed analytics.
    """
    try:
        # Verify user has access to this team
        if not await team_service.user_has_team_access(
                db=db,
                team_id=team_id,
                user_id=current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="Access denied - you must be a team member to view team statistics"
            )

        # Determine user role within the team and return appropriate response
        is_team_lead = await team_service.user_is_team_lead(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        )

        if is_team_lead:
            # Team lead gets full dashboard view with all member statistics
            return await team_service.get_team_dashboard_statistics(
                db=db,
                team_id=team_id
            )
        else:
            # Regular team members get personal view with team comparison
            return await team_service.get_personal_team_statistics(
                db=db,
                team_id=team_id,
                user_id=current_user.id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team statistics for team {team_id}, user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")