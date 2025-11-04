"""
Team Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class TeamMemberRoleEnum(str, Enum):
    """Team member roles"""
    TEAM_LEAD = "team_lead"
    MEMBER = "member"


class UserBasicInfo(BaseModel):
    """Basic user info for team member"""
    id: str
    username: str
    full_name: str
    email: str

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """Team member response"""
    id: str
    user_id: str
    team_id: str
    role: TeamMemberRoleEnum
    joined_at: datetime
    user: Optional[UserBasicInfo] = None

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Team response with members"""
    id: str
    name: str
    description: Optional[str] = None
    team_lead_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse]
    join_code: Optional[str] = None

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    """Team creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    team_lead_id: Optional[str] = None  # Will default to current user


class TeamUpdate(BaseModel):
    """Team update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    team_lead_id: Optional[str] = None
    is_active: Optional[bool] = None


class JoinTeamRequest(BaseModel):
    """Join team by code request"""
    join_code: str = Field(..., min_length=1)


class UpdateTeamMemberRequest(BaseModel):
    """Update team member role request"""
    role: TeamMemberRoleEnum


class JoinCodeResponse(BaseModel):
    """Join code generation response"""
    join_code: str
    expires_at: datetime
    team_id: str
    message: str


class TeamDeletionResponse(BaseModel):
    """Team deletion response"""
    success: bool
    message: str
    deleted_team_id: str
    affected_learning_paths_count: int
    affected_members_count: int


class RemoveMemberResponse(BaseModel):
    """Remove team member response"""
    success: bool
    message: str
    removed_user_id: str
    team_id: str

PlatformTimeSplit = Dict[str, int]

class ProgressSummary(BaseModel):
    """Simplified summary of progress across courses"""
    completed: Dict[str, int] = Field(..., description="Completed courses count")
    in_progress: Dict[str, int] = Field(..., description="In progress courses count")


class CurrentUserStatistics(BaseModel):
    """Statistical data specific to the current user"""
    user_id: str = Field(..., description="User ID")
    full_name: str = Field(..., description="User's full name")
    user_team_learning_time_minutes: int = Field(..., description="User's total team learning time in minutes")
    learning_path_progress_summary: ProgressSummary = Field(..., description="Learning path progress summary")
    platform_split_minutes: PlatformTimeSplit = Field(..., description="Time distribution across platforms")


class TeamComparisonStatistics(BaseModel):
    """Comparative data at team level"""
    rank: int = Field(..., description="User's rank within the team")
    total_members: int = Field(..., description="Total number of team members")
    average_learning_time_minutes: int = Field(..., description="Team average learning time in minutes")


class PersonalTeamStatisticsApiResponse(BaseModel):
    """Final unified object returned by API for team member view"""
    user_stats: CurrentUserStatistics = Field(..., description="Current user statistics")
    team_comparison_stats: TeamComparisonStatistics = Field(..., description="Team comparison statistics")


class LearningPathSummary(BaseModel):
    """Detailed summary of courses for a member, grouped by status"""
    completed: Dict[str, object] = Field(..., description="Completed paths data")
    in_progress: Dict[str, object] = Field(..., description="In progress paths data")
    unstarted: Dict[str, object] = Field(..., description="Unstarted paths data")

    def __init__(self, **data):
        # Ensure proper structure with count and paths
        for status in ['completed', 'in_progress', 'unstarted']:
            if status in data and isinstance(data[status], dict):
                if 'count' not in data[status]:
                    data[status]['count'] = 0
                if 'paths' not in data[status]:
                    data[status]['paths'] = []
        super().__init__(**data)


class TeamMember(BaseModel):
    """Complete data for a single team member"""
    user_id: str = Field(..., description="User ID")
    full_name: str = Field(..., description="User's full name")
    team_learning_time_minutes: int = Field(..., description="Team learning time in minutes")
    learning_path_progress_summary: LearningPathSummary = Field(..., description="Learning path progress summary")


class OverallProgress(BaseModel):
    """Progress statistics at the entire team level"""
    overall_completion_percentage: float = Field(..., description="Overall team completion percentage")
    completed_user_lp_assignments: int = Field(..., description="Completed user learning path assignments")
    in_progress_user_lp_assignments: int = Field(..., description="In progress user learning path assignments")
    unstarted_user_lp_assignments: int = Field(..., description="Unstarted user learning path assignments")


class TeamDashboardApiResponse(BaseModel):
    """Final unified object returned by API for team dashboard"""
    overall_progress: OverallProgress = Field(..., description="Overall team progress statistics")
    member_list: List[TeamMember] = Field(..., description="List of team members (backend should return sorted)")
    platform_summary: Dict[str, int] = Field(..., description="Platform time summary, e.g., {'YouTube': 4500}")

class TeamStats(BaseModel):
    """Team statistics for dashboard"""
    total_paths: int = Field(..., description="Total number of learning paths in the team")
    total_members: int = Field(..., description="Total number of team members")
    avg_progress_percentage: float = Field(..., description="Average progress percentage across all members")
