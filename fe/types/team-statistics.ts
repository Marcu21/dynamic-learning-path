export type PlatformTimeSplit = Record<string, number>;

export interface ProgressSummary {
  completed: { count: number };
  in_progress: { count: number };
}

export interface CurrentUserStatistics {
  user_id: string;
  full_name: string;
  user_team_learning_time_minutes: number;
  learning_path_progress_summary: ProgressSummary;
  platform_split_minutes: PlatformTimeSplit;
}

export interface TeamComparisonStatistics {
  rank: number;
  total_members: number;
  average_learning_time_minutes: number;
}

export interface PersonalTeamStatisticsApiResponse {
  user_stats: CurrentUserStatistics;
  team_comparison_stats: TeamComparisonStatistics;
}

export interface PathDetails {
  id: string;
  title: string;
}

export interface LearningPathSummary {
  completed: {
    count: number;
    paths: PathDetails[];
  };
  in_progress: {
    count: number;
    paths: PathDetails[];
  };
  unstarted: {
    count: number;
    paths: PathDetails[];
  };
}

export interface TeamMember {
  user_id: string;
  full_name: string;
  team_learning_time_minutes: number;
  learning_path_progress_summary: LearningPathSummary;
}

export interface OverallProgress {
  overall_completion_percentage: number;
  completed_user_lp_assignments: number;
  in_progress_user_lp_assignments: number;
  unstarted_user_lp_assignments: number;
}

export interface TeamDashboardApiResponse {
  overall_progress: OverallProgress;
  member_list: TeamMember[];
  platform_summary: Record<string, number>;
}