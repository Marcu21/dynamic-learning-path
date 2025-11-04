import {LearningPath, Module} from "@/types/learning-paths";
import type {UserStatistics} from "@/types/user-statistics";

export interface UseLearningPathOptions {
  pathId: string;
  userId: string;
  teamId?: string;
}

export interface UseLearningPathReturn {
  currentPath: LearningPath | null;
  modules: Module[];
  currentModule: Module | null;
  completedModules: Set<number>;
  loading: boolean;
  error: string | null;
  moduleCompletionLoading: Set<number>;
  completionSuccessMessage: string | null;
  showCertificate: boolean;
  // Actions
  markModuleComplete: (moduleId: number) => Promise<void>;
  skipModule: (moduleId: number) => Promise<void>;
  setCurrentModule: (module: Module | null) => void;
  setShowCertificate: (show: boolean) => void;
  refreshPath: () => Promise<void>;
}

export interface UseUserStatisticsOptions {
  userId?: string;
  autoLoad?: boolean;
  refreshInterval?: number;
  useLocalStorage?: boolean;
}

export interface UseUserStatisticsReturn {
  statistics: UserStatistics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  // Actions
  refresh: () => Promise<void>;
  clearError: () => void;
  clearCache: () => void;
}

export interface UsePaginationProps {
  totalPages: number;
  siblingCount?: number;
  currentPage: number;
}