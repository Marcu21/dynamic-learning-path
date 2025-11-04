import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { UserStatistics } from '@/types/user-statistics';
import type { UseUserStatisticsOptions, UseUserStatisticsReturn } from '@/hooks/types';

// Local Storage helpers
const STORAGE_KEYS = {
  USER_STATISTICS: (userId: string) => `user_statistics_${userId}`,
  LAST_UPDATED: (userId: string) => `statistics_last_updated_${userId}`
};

const saveToLocalStorage = (userId: string, statistics: UserStatistics) => {
  try {
    localStorage.setItem(STORAGE_KEYS.USER_STATISTICS(userId), JSON.stringify(statistics));
    localStorage.setItem(STORAGE_KEYS.LAST_UPDATED(userId), new Date().toISOString());
  } catch (error) {}
};

const loadFromLocalStorage = (userId: string): { statistics: UserStatistics | null; lastUpdated: Date | null } => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.USER_STATISTICS(userId));
    const lastUpdatedStr = localStorage.getItem(STORAGE_KEYS.LAST_UPDATED(userId));

    return {
      statistics: data ? JSON.parse(data) : null,
      lastUpdated: lastUpdatedStr ? new Date(lastUpdatedStr) : null
    };
  } catch (error) {
    return { statistics: null, lastUpdated: null };
  }
};

const clearLocalStorage = (userId: string) => {
  try {
    localStorage.removeItem(STORAGE_KEYS.USER_STATISTICS(userId));
    localStorage.removeItem(STORAGE_KEYS.LAST_UPDATED(userId));
  } catch (error) {}
};

export type { UseUserStatisticsOptions, UseUserStatisticsReturn };

export function useUserStatistics({
  userId,
  autoLoad = true,
  refreshInterval,
  useLocalStorage = true
}: UseUserStatisticsOptions = {}): UseUserStatisticsReturn {
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Load user statistics from API
  const loadStatistics = useCallback(async (skipCache = false) => {
    if (!userId) {
      setError('User ID is required');
      return;
    }

    // Try to load from localStorage first if enabled and not skipping cache
    if (useLocalStorage && !skipCache) {
      const cached = loadFromLocalStorage(userId);
      if (cached.statistics) {
        setStatistics(cached.statistics);
        setLastUpdated(cached.lastUpdated);
        // Still fetch fresh data in background but don't show loading
        loadStatistics(true);
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const stats = await api.getUserStatistics(userId) as UserStatistics;

      setStatistics(stats);
      const now = new Date();
      setLastUpdated(now);

      // Save to localStorage if enabled
      if (useLocalStorage) {
        saveToLocalStorage(userId, stats);
      }


    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user statistics');
    } finally {
      setLoading(false);
    }
  }, [userId, useLocalStorage]);

  // Refresh statistics (alias for loadStatistics with public interface)
  const refresh = useCallback(async () => {
    await loadStatistics(true); // Force refresh, skip cache
  }, [loadStatistics]);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Clear cache
  const clearCache = useCallback(() => {
    if (userId && useLocalStorage) {
      clearLocalStorage(userId);
      setStatistics(null);
      setLastUpdated(null);
    }
  }, [userId, useLocalStorage]);

  // Autoload on mount and when userId changes
  useEffect(() => {
    if (autoLoad && userId) {
      loadStatistics();
    }
  }, [autoLoad, userId, loadStatistics]);

  // Set up refresh interval if specified
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0 && userId) {
      const interval = setInterval(() => {
        if (!loading) { // Only refresh if not already loading
          loadStatistics(true); // Force refresh for interval updates
        }
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval, userId, loading, loadStatistics]);

  return {
    statistics,
    loading,
    error,
    lastUpdated,
    // Actions
    refresh,
    clearError,
    clearCache,
  };
}