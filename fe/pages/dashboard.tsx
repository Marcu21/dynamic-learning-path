import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { useNotifications } from '@/context/NotificationContext';
import LearningPathDashboard from '@/components/dashboard/PersonalDashboard';
import { UserProfile } from '@/types/user';
import { useRouter } from 'next/router';
import { DashboardPageProps } from '@/types/dashboard';

export default function Dashboard({ generationState }: DashboardPageProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { generationCompletionEvent, clearGenerationEvent } = useNotifications();
  const router = useRouter();
  const [dashboardRefreshKey, setDashboardRefreshKey] = useState(0);

  const userProfile = useMemo<UserProfile>(() => ({
    name: "User",
    experience_level: "intermediate",
    learning_styles: ["visual"],
    available_time: 60,
    interests: ["programming", "web development"],
    preferred_content_types: [],
    target_level: "beginner",
    platforms: [],
  }), []);

  const isGenerating = generationState.inProgress && generationState.teamId === null;

  useEffect(() => {
    if (generationCompletionEvent) {
      if (generationCompletionEvent.teamId === null || generationCompletionEvent.teamId === undefined) {
        setDashboardRefreshKey(prev => prev + 1);
        clearGenerationEvent();
      }
    }
  }, [generationCompletionEvent, clearGenerationEvent]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (typeof window !== 'undefined') {
        router.replace('/login');
    }
    return null;
  }

  return (
    <motion.div
      className="min-h-screen bg-gray-50 relative overflow-hidden"
      initial="hidden"
      animate="visible"
      variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 }}}
    >
      <motion.div>
        <LearningPathDashboard
          userProfile={userProfile}
          userId={user?.id}
          refreshKey={dashboardRefreshKey}
          isGenerating={isGenerating}
          currentStatus={generationState.currentStatus}
          generatedPathId={generationState.generatedPathId}
        />
      </motion.div>
    </motion.div>
  );
}