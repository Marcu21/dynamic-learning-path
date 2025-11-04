"use client"
import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect, memo } from "react"
import * as anim from "@/components/learning-path/LearningPathDisplay/animations"
import * as styles from "@/components/learning-path/LearningPathDisplay/styles"
import type { Module } from "@/types/learning-paths"
import ModuleDropdown from "@/components/learning-path/ModuleDropdown"
import { GeneratingModuleCard } from "@/components/learning-path/GeneratingModuleCard"
import { useChatLocationUpdater } from "@/context/ChatContext"
import type { LearningPathDisplayProps } from "@/components/learning-path/LearningPathDisplay/types"

function LearningPathDisplay({
  path,
  modules,
  title,
  estimatedDays,
  onModuleSelect,
  onModuleComplete,
  onInsertModule,
  currentModule,
  completedModules,
  moduleCompletionLoading = new Set(),
  userId,
  learningPathId,
  onQuizComplete,
  isTeamLearningPath = false,
  isTeamLead = false,
  generatingModules = new Set(),
  isGeneratingModules = false,
}: LearningPathDisplayProps) {
  const { setLearningPathContext } = useChatLocationUpdater()
  const { setLearningPathContextForce } = useChatLocationUpdater()


  useEffect(() => {
    if (learningPathId) setLearningPathContext(learningPathId)
  }, [learningPathId, setLearningPathContext])

  const [expandedModuleId, setExpandedModuleId] = useState<number | null>(null)
  const [localGeneratingModules, setLocalGeneratingModules] = useState<Set<number | string>>(new Set())

  useEffect(() => {
    if (expandedModuleId === null && learningPathId) {
      setLearningPathContextForce (learningPathId)
    }
  }, [expandedModuleId, learningPathId, setLearningPathContextForce ])

  const getModuleStatus = (m: Module): "completed" | "current" | "pending" => {
    const isCompleted = completedModules.has(m.id)
    const isCurrent = currentModule?.id === m.id
    if (isCompleted) return "completed"
    if (isCurrent) return "current"
    return "pending"
  }

  const handleModuleComplete = async (module: Module) => {
    await onModuleComplete(module)
    const updatedCompletedModules = new Set(completedModules)
    updatedCompletedModules.add(module.id)
    const currentIndex = modules.findIndex(m => m.id === module.id)
    modules.find((m, index) => {
      const isCompleted = updatedCompletedModules.has(m.id)
      return index > currentIndex && !isCompleted
    });
  }

  const handleInsertModule = async (afterIndex: number, query: string, platformName?: string) => {
    if (onInsertModule) {
      const insertionId = `after-${afterIndex}` // Use consistent ID format
      setLocalGeneratingModules(prev => new Set(prev).add(insertionId))

      try {
        await onInsertModule(afterIndex, query, platformName)
      } catch (error) {
        // Remove the generating state on error
        setLocalGeneratingModules(prev => {
          const newSet = new Set(prev)
          newSet.delete(insertionId)
          return newSet
        })
      }
    }
  }

  // Clear generating states when new modules appear
  useEffect(() => {
    if (modules.length > 0) {
      setLocalGeneratingModules(new Set())
    }
  }, [modules.length])

  return (
    <motion.div
      className={styles.wrapper}
      initial="hidden"
      animate="visible"
      variants={anim.listVariants}
    >
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>
            {title || "Your Learning Path"}
            {isTeamLearningPath && (
              <span className="ml-2 px-2 py-1 text-sm align-middle inline-block bg-primary-light text-primary-dark rounded-full">
                Team Path
              </span>
            )}
          </h2>
          <p className={styles.estimate}>
            Estimated: {estimatedDays || path.estimated_days} days
          </p>
        </div>
        <div className={styles.moduleCount}>
          <div className={styles.countNumber}>
            {completedModules.size}/{modules.length}
          </div>
          <div className={styles.countLabel}>Modules</div>
        </div>
      </div>

      <div className={styles.list}>
        {/* Show generating card if entire path is generating */}
        {isGeneratingModules && modules.length === 0 && (
          <GeneratingModuleCard key="path-generating" />
        )}

        {modules.map((module, index) => {
          const status = getModuleStatus(module)
          const locked = index > 0 && !completedModules.has(modules[index - 1].id)
          const insertionId = `after-${index}` // Match the ID format from parent component

          return (
            <div key={module.id}>
              <ModuleDropdown
                module={module}
                index={index}
                status={status}
                locked={locked}
                onModuleSelect={onModuleSelect}
                onMarkComplete={handleModuleComplete}
                onInsertModule={handleInsertModule}
                isExpanded={expandedModuleId === module.id}
                onToggleExpanded={(isExpanded) => setExpandedModuleId(isExpanded ? module.id : null)}
                isCompletionLoading={moduleCompletionLoading.has(module.id)}
                userId={userId}
                learningPathId={learningPathId}
                onQuizComplete={onQuizComplete}
                isTeamLearningPath={isTeamLearningPath}
                isTeamLead={isTeamLead}
              />

              {/* Show generating card after this module if it's being generated */}
              <AnimatePresence>
                {(localGeneratingModules.has(insertionId) || generatingModules.has(insertionId)) && (
                  <>
                    <GeneratingModuleCard key={`generating-${insertionId}`} />
                  </>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}

export default memo(LearningPathDisplay);