export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface ChatRequest {
  user_id: string;
  question: string;
  location: string;
  learning_path_id?: number;
  module_id?: number;
  quiz_id?: number;
  quiz_attempt_id?: number;
  team_id?: string;
}

export interface ChatInitResponse {
  task_id: string;
  stream_channel: string;
  message: string;
  status: string;
  user_context: {
    location: string;
    learning_path_id: number | null;
    module_id: number | null;
    quiz_id: number | null;
    session_id: string;
  };
  estimated_completion_time: number;
}

export interface ChatReadyResponse {
  status: string;
  message: string;
  ready_key: string;
}

export interface StreamMessage {
  type: 'connected' | 'content' | 'status' | 'complete' | 'error' | 'metadata';
  data?: any;
  task_id?: string;
  timestamp?: number;
  user_id?: string;
  session_id?: string;
  progress?: number;
  channel?: string;
}