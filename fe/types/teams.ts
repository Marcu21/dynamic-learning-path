import {PreferencesCreate} from "@/types/learning-paths";

export interface Team {
  id: string;
  name: string;
  description?: string;
  team_lead_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  members: TeamMember[];
  join_code?: string; // New field for join codes
}

export interface TeamMember {
  id: string;
  user_id: string;
  team_id: string;
  role: TeamMemberRole;
  joined_at: string;
  user?: {
    id: string;
    username: string;
    full_name: string;
    email: string;
  };
}

export enum TeamMemberRole {
  TEAM_LEAD = "team_lead",
  MEMBER = "member"
}

export interface TeamCreate {
  name: string;
  description?: string;
  team_lead_id: string;
}

export interface TeamUpdate {
  name?: string;
  description?: string;
  team_lead_id?: string;
  is_active?: boolean;
}

export interface JoinTeamRequest {
  join_code: string;
}

export interface TeamLearningPath {
  id: number;
  title: string;
  description: string;
  user_id: string;
  team_id: string;
  estimated_days: number;
  is_public: boolean;
  total_modules: number;
  completion_percentage?: number;
  created_at: string;
  updated_at: string;
}

export interface GenerationState {
  inProgress: boolean;
  teamId: string | null;
  taskId: string | null;
}

export interface TeamPageProps {
  generationState: GenerationState;
  startGeneration: (preferences: PreferencesCreate, teamId: string | null) => void;
}
