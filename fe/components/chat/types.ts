export interface ChatMessage {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  isStreaming?: boolean
}

export interface ChatAssistantProps {
  userId: string
  location: string
  learningPathId?: number
  moduleId?: number
  quizId?: number
  quizAttemptId?: number
  teamId?: string;
  className?: string
}

export type LocationContext =
  | "dashboard"
  | "learning_path"
  | "module"
  | "quiz"
  | "quiz_attempt_active"
  | "review_answers"

export interface IntegratedChatAssistantProps {
  userId: string;
  className?: string;
  location?: string;
  learningPathId?: number;
  moduleId?: number;
  quizId?: number;
  quizAttemptId?: number;
  teamId?: string;
}