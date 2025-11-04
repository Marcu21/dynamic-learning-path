import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { useNotifications } from '@/context/NotificationContext';
import ProfileSetup from '@/components/learning-path/ProfileSetup';
import ParticlesBackground from '@/components/background/ParticlesBackground';
import { PreferencesCreate } from '@/types/learning-paths';
import { UserProfile, LearningGoal } from '@/types/user';
import GenerationLoadingScreen from '@/components/dashboard/PersonalDashboard/GenerationLoadingScreen';
import { NewPathPageProps } from '@/types/learning-paths';

const anim = {
  fadeSlide: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  }
};

const generatingMessages = [
  "Analyzing your preferences...",
  "Creating personalized modules...",
  "Structuring your learning journey...",
];

export default function NewPathPage({ generationState, startGeneration, resetGeneration }: NewPathPageProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const { generationCompletionEvent, clearGenerationEvent } = useNotifications();

  const isGenerating = generationState.inProgress && generationState.teamId === null;

  function mapLearningStyleForAPI(style: string): "visual" | "auditory" | "kinesthetic" | "reading-writing" {
    switch (style) {
      case "visual": case "auditory": case "kinesthetic":
        return style;
      case "reading":
        return "reading-writing";
      default:
        return "visual";
    }
  }

  const handleProfileSetup = async (profile: UserProfile, goal: LearningGoal) => {
    const preferences: PreferencesCreate = {
      subject: goal.goal,
      experience_level: profile.experience_level as "beginner" | "intermediate" | "advanced",
      learning_styles: profile.learning_styles.map(mapLearningStyleForAPI),
      preferred_platforms: profile.platforms || [],
      study_time_minutes: profile.available_time,
      goals: goal.goal
    };
    startGeneration(preferences);
  };

  const handleCancel = () => {
    router.push('/dashboard');
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  useEffect(() => {
    if (generationCompletionEvent && !generationCompletionEvent.teamId) {
      const pathId = generationCompletionEvent.learning_path.id;
      if (pathId) {
        router.push(`/paths/${pathId}`);
        clearGenerationEvent();
      }
    }
  }, [generationCompletionEvent, clearGenerationEvent, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (typeof window !== "undefined") {
      router.push('/login');
    }
    return null;
  }

  if (isGenerating) {
    return (
      <div className="min-h-screen relative overflow-hidden flex items-center justify-center p-4">
        <ParticlesBackground />
        <GenerationLoadingScreen
          messages={generatingMessages}
          onBackToDashboard={handleBackToDashboard}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
        <ParticlesBackground />
        <motion.div
            className="relative z-10 flex items-center justify-center min-h-screen p-4"
            initial="hidden"
            animate="visible"
            variants={anim.fadeSlide}
        >
            <ProfileSetup
                onComplete={handleProfileSetup}
                onCancel={handleCancel}
                username={user?.username || user?.email || undefined}
            />
        </motion.div>
    </div>
  );
}