export interface LearningPath {
    id: number;
    user_id: string;
    title: string;
    description: string;
    estimated_days: number;
    completion_percentage: number;
    created_at?: string;
    updated_at?: string;
}

export interface Module {
    id: number;
    learning_path_id: number;
    platform_id: number;
    platform_name: string;
    title: string;
    description: string;
    learning_objectives?: string[];
    duration: number; // in minutes
    order_index: number;
    content_url: string;
    difficulty: "EASY" | "MEDIUM" | "HARD" | "EXPERT";
    learning_style: "VISUAL" | "AUDITORY" | "KINESTHETIC" | "READING_WRITING";
    completed?: boolean;
    created_at?: string;
    is_inserted?: boolean; // Indicates if the module was inserted by the user
}

// For frontend display and selection
export interface LearningPathFE {
    id: number;
    user_id: string;
    title: string;
    description?: string;
    estimated_days: number;
    completion_percentage: number;
    created_at?: string;
}

// For AI Generation & Streaming
export interface PreferencesCreate {
    subject: string;
    experience_level: "beginner" | "intermediate" | "advanced";
    learning_styles: ("visual" | "auditory" | "kinesthetic" | "reading-writing")[];
    preferred_platforms: string[];
    study_time_minutes: number;
    goals: string;
}

export interface GenerationState {
  inProgress: boolean;
  teamId: string | null;
}

export interface NewPathPageProps {
  generationState: GenerationState;
  startGeneration: (preferences: PreferencesCreate, teamId?: string | null) => void;
  resetGeneration: () => void;
}