import type {LearningPath, Module} from "@/types/learning-paths";

export interface LearningPathDisplayProps {
  path: LearningPath
  modules: Module[]
  title?: string
  estimatedDays?: number
  onModuleSelect: (m: Module) => void
  onModuleComplete: (m: Module) => Promise<void>
  onInsertModule?: (afterIndex: number, query: string, platformName?: string) => Promise<void>
  currentModule: Module | null
  completedModules: Set<number>
  moduleCompletionLoading?: Set<number>
  userId?: string
  learningPathId?: number
  onQuizComplete?: () => void
  isTeamLearningPath?: boolean
  isTeamLead?: boolean
  generatingModules?: Set<number | string> // Track which modules/insertions are being generated
  isGeneratingModules?: boolean // Track if the entire path is being generated
}