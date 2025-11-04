import type { LearningPathFE } from "@/types/learning-paths";

export interface PathSelectorProps {
  paths: LearningPathFE[];
  onSelectPath: (path: LearningPathFE) => void;
  currentPathId?: number;
}
