import { type LucideIcon } from "lucide-react";

export interface UserProfile {
  name: string;
}

export interface LearningPathFE {
  id: number;
  user_id: string;
  title: string;
  description: string;
  estimated_days: number;
  completion_percentage: number;
}

export interface Category {
  id: string;
  label: string;
  icon: LucideIcon;
}

export interface LearningPathDashboardProps {
  onSelectPath?: (path: LearningPathFE) => void;
  onCreateNewPath?: () => void;
  userProfile: UserProfile;
  userId?: string;
  refreshKey?: number;
  isGenerating?: boolean;
  currentStatus?: string;
  generatedPathId?: string | null;
}

export interface PathCardProps {
  path: LearningPathFE;
  index: number;
  openMenuId: number | null;
  toggleMenu: (pathId: number, e: React.MouseEvent) => void;
  handleDeletePath: (path: LearningPathFE, e: React.MouseEvent) => void;
}