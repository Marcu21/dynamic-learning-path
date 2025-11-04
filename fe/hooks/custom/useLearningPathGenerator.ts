import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';
import { useNotifications } from '@/context/NotificationContext';
import type { PreferencesCreate } from '@/types/learning-paths';
import type { GenerationResponse, UseLearningPathGeneratorOptions, UseLearningPathGeneratorReturn } from '@/types/path-generation';

export type { UseLearningPathGeneratorOptions, UseLearningPathGeneratorReturn };

export function useLearningPathGenerator({ 
  userId, 
  teamId: defaultTeamId
}: UseLearningPathGeneratorOptions = {}): UseLearningPathGeneratorReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [generatedPathId, setGeneratedPathId] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState('');
  const [taskInfo, setTaskInfo] = useState<GenerationResponse | null>(null);
  const [generationContext, setGenerationContext] = useState<{ taskId: string | null; teamId: string | null }>({ taskId: null, teamId: null });

  const { generationCompletionEvent} = useNotifications();

  const resetGeneration = useCallback(() => {
    setIsGenerating(false);
    setProgress(0);
    setError(null);
    setGeneratedPathId(null);
    setCurrentStatus('');
    setTaskInfo(null);
    setGenerationContext({ taskId: null, teamId: null });
  }, []);

  useEffect(() => {
    if (generationCompletionEvent?.learning_path?.id) {
      setGeneratedPathId(generationCompletionEvent.learning_path.id.toString());
      resetGeneration();
    }
  }, [generationCompletionEvent, resetGeneration]);

  const startGeneration = useCallback(async (
    preferences: PreferencesCreate,
    dynamicTeamId?: string | null
  ) => {
    if (isGenerating) return;
    if (!userId) {
      setError('User ID is required for generation');
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setError(null);
    setGeneratedPathId(null);
    setCurrentStatus('PENDING');
    setTaskInfo(null);

    try {
      let result: GenerationResponse;
      const taskTeamId = (dynamicTeamId !== undefined ? dynamicTeamId : defaultTeamId) ?? null;

      if (taskTeamId) {
        const teamPreferences = { ...preferences, team_id: taskTeamId };
        result = await api.startTeamLearningPathGeneration(teamPreferences);
      } else {
        result = await api.startLearningPathGeneration(preferences);
      }

      setGenerationContext({ taskId: result.task_id, teamId: taskTeamId });
      setTaskInfo(result);
      setCurrentStatus('STARTED');
      setProgress(5);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation');
      setIsGenerating(false);
      setCurrentStatus('FAILED');
    }
  }, [isGenerating, userId, defaultTeamId]);

  return {
    isGenerating,
    progress,
    error,
    generatedPathId,
    currentStatus,
    taskInfo,
    startGeneration,
    resetGeneration,
    generationContext,
  };
}