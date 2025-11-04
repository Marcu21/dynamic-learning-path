import {ReactNode} from "react";
import {User} from "@/types/user";
import type { Notification as AppNotification } from '@/types/notifications';

// === Auth Context ===
export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  validateAuth: () => Promise<boolean>;
}

export interface AuthProviderProps {
  children: ReactNode;
}

// === Chat Context ===
export type LocationKind =
  | 'dashboard'
  | 'learning_path'
  | 'module'
  | 'quiz'
  | 'quiz_attempt_active'
  | 'review_answers';

export interface ChatContextValue {
  // Location tracking for context-aware chat
  currentLocation: LocationKind;
  learningPathId?: number;
  moduleId?: number;
  quizId?: number;
  quizAttemptId?: number;

  // Methods to update context
  setLocation: (location: LocationKind) => void;
  setLearningPathId: (id?: number) => void;
  setModuleId: (id?: number) => void;
  setQuizId: (id?: number) => void;
  setQuizAttemptId: (id?: number) => void;

  // Complete context update
  updateChatContext: (context: Partial<ChatContextValue>) => void;
  updateChatContextAllowDowngrade: (context: Partial<ChatContextValue>) => void;
}

export interface ChatProviderProps {
  children: ReactNode;
  initialLocation?: LocationKind;
}


// === Notification Context ===
export interface SelectionEvent {
  pathId: number;
  teamId?: string;
  timestamp: number;
}

export interface GenerationCompletionEvent {
  learning_path: any;
  teamId?: string;
  timestamp: number;
}

export interface NotificationContextType {
  notifications: AppNotification[];
  unreadCount: number;
  addNotification: (message: string, pathId?: number, teamId?: string) => void;
  markAllAsRead: () => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  selectionEvent: SelectionEvent | null;
  selectPath: (pathId: number, teamId?: string) => void;
  clearSelection: () => void;
  isSoundEnabled: boolean;
  toggleSound: () => void;
  // Task completion handler
  onTaskCompleted?: (taskId: string, result: any) => void;
  registerTaskCompletionHandler: (handler: (taskId: string, result: any) => void) => void;
  // Generation completion event
  generationCompletionEvent: GenerationCompletionEvent | null;
  clearGenerationEvent: () => void;
}