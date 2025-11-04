import type { PreferencesCreate } from "@/types/learning-paths";

export interface GenerationResponse {
  task_id: string;
  stream_channel?: string;
  status: string;
  user_id: string;
  subject: string;
  estimated_duration_minutes: number;
  created_at: string;
}

export interface UseLearningPathGeneratorOptions {
  userId?: string;
  teamId?: string | null;
}

export interface UseLearningPathGeneratorReturn {
  isGenerating: boolean;
  progress: number;
  error: string | null;
  generatedPathId: string | null;
  currentStatus: string;
  // Task information
  taskInfo: GenerationResponse | null;
  // Actions
  startGeneration: (preferences: PreferencesCreate, dynamicTeamId?: string | null) => Promise<void>;
  resetGeneration: () => void;
  generationContext: { taskId: string | null; teamId: string | null };
}
