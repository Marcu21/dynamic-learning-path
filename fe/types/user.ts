export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
    name: string;
    learning_styles: string[];
    experience_level: string;
    preferred_content_types: string[];
    available_time: number;
    interests: string[];
    target_level: string;
    platforms?: string[];
}

export interface LearningGoal {
    goal: string;
    target_completion_date?: string;
    priority: string;
}
