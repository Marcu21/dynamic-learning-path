import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { LearningPath, Module } from '@/types/learning-paths';
import { UseLearningPathOptions, UseLearningPathReturn } from '@/hooks/types';

export const useLearningPath = ({ pathId, userId, teamId }: UseLearningPathOptions): UseLearningPathReturn => {
  const [currentPath, setCurrentPath] = useState<LearningPath | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [currentModule, setCurrentModule] = useState<Module | null>(null);
  const [completedModules, setCompletedModules] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [moduleCompletionLoading, setModuleCompletionLoading] = useState<Set<number>>(new Set());
  const [completionSuccessMessage, setCompletionSuccessMessage] = useState<string | null>(null);
  const [showCertificate, setShowCertificate] = useState(false);

  const refreshPath = useCallback(async () => {
    if (!pathId || !userId) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch learning path using the API helper
      const pathResponse = await api.getLearningPath(parseInt(pathId));
      setCurrentPath(pathResponse.learning_path);

      // Fetch modules for the path
      const pathModules: Module[] = pathResponse.modules || [];
      setModules(pathModules);

      // Fetch user progress
      const progressResponse = await api.getLearningPathProgress(userId, parseInt(pathId));
      const completedModuleIds = new Set<number>(progressResponse.completed_modules || []);
      setCompletedModules(completedModuleIds);

      // Find first incomplete module as current
      const firstIncomplete = pathModules.find(
        module => !completedModuleIds.has(module.id)
      );
      setCurrentModule(firstIncomplete || null);

    } catch (err) {
      setError('Failed to load learning path. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [pathId, userId, teamId]);

  // Mark module as complete
  const markModuleComplete = useCallback(async (moduleId: number) => {
    if (!userId || !pathId) return;

    setModuleCompletionLoading(prev => new Set([...prev, moduleId]));

    try {
      await api.markModuleComplete(moduleId, userId);

      // Update local state
      setCompletedModules(prev => new Set([...prev, moduleId]));
      setCompletionSuccessMessage('Module completed successfully!');

      // Clear success message after 3 seconds
      setTimeout(() => setCompletionSuccessMessage(null), 3000);

      // Check if all modules are completed for certificate
      if (modules.length > 0) {
        const allCompleted = modules.every(
          module => completedModules.has(module.id) || module.id === moduleId
        );
        if (allCompleted) {
          setShowCertificate(true);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete module');
    } finally {
      setModuleCompletionLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete(moduleId);
        return newSet;
      });
    }
  }, [userId, pathId, modules, completedModules]);

  // Skip module (mark as complete without doing the work)
  const skipModule = useCallback(async (moduleId: number) => {
    await markModuleComplete(moduleId);
  }, [markModuleComplete]);

  // Load data on mount and when dependencies change
  useEffect(() => {
    refreshPath();
  }, [refreshPath]);

  // Clear success message when component unmounts
  useEffect(() => {
    return () => {
      if (completionSuccessMessage) {
        setCompletionSuccessMessage(null);
      }
    };
  }, [completionSuccessMessage]);

  return {
    currentPath,
    modules,
    currentModule,
    completedModules,
    loading,
    error,
    moduleCompletionLoading,
    completionSuccessMessage,
    showCertificate,
    // Actions
    markModuleComplete,
    skipModule,
    setCurrentModule,
    setShowCertificate,
    refreshPath,
  };
};

export type { UseLearningPathOptions, UseLearningPathReturn };
