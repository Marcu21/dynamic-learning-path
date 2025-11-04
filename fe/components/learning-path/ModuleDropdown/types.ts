import type {Module} from "@/types/learning-paths";

export interface ModuleDropdownProps {
  module: Module
  index: number
  status: "completed" | "current" | "pending"
  locked: boolean
  onModuleSelect: (module: Module) => void
  onMarkComplete: (module: Module) => Promise<void>
  onInsertModule?: (afterIndex: number, query: string, platformName?: string) => Promise<void>
  isExpanded?: boolean
  onToggleExpanded?: (isExpanded: boolean) => void
  isCompletionLoading?: boolean
  userId?: string
  learningPathId?: number
  onQuizComplete?: () => void
  isTeamLearningPath?: boolean
  isTeamLead?: boolean
}