export interface UserStatistics {
  // Common fields
  user_id: string;

  // Streak fields
  streak_days?: number; // number of consecutive days the user has been active
  user_created_at?: string | null; // date when the user was created

  // Content Completion fields
  completed_learning_paths?: number; // number of learning paths completed by the user
  modules_completed?: number; // number of modules completed by the user
  skill_points_earned?: number; // total skill points earned by the user
  quizzes_completed?: number; // number of quizzes completed by the user

  // Where you stand
  user_total_minutes?: number; // total minutes spent by the user
  community_average_minutes?: number; // average minutes spent by the community

  // Daily Learning Data
  learning_time_data?: DailyLearningTimeData; // maps date to minutes spent learning

  // Platform Time Summary
  platform_time_summary?: PlatformTimeSummaryData; // maps platform to percentage of time spent on it

  // Key Insights fields
  top_percentile_time?: number; // top what percentile the user is in based on time spent
  community_impact?: number; // user time spent / total time spent by the community
  content_coverage?: number; // percentage of content the user has completed of its own learning paths
}

// Additional type aliases for specific data structures
export type DailyLearningTimeData = Record<string, number>;
export type PlatformTimeSummaryData = Record<string, number>;

export interface Team {
  id: string
  name: string
  avatar?: string
  members?: any[]
}

export interface StatisticsChartsProps {
  statistics: UserStatistics
  userId: string
  timePeriod: number
}
