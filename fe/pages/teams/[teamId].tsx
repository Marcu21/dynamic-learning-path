import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { teamApi } from '@/lib/api';
import TeamDashboard from '@/components/dashboard/TeamDashboard';
import { PreferencesCreate } from '@/types/learning-paths';
import { useNotifications } from '@/context/NotificationContext';
import { TeamPageProps } from '@/types/teams';

const anim = {
  fadeSlide: {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  }
};

export default function TeamPage({ generationState, startGeneration }: TeamPageProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { teamId } = router.query;

  const [, setTeamInfo] = useState<any>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const { generationCompletionEvent, clearGenerationEvent } = useNotifications();


  useEffect(() => {
    if (teamId && typeof teamId === 'string') {
      teamApi.getTeam(teamId)
        .then(teamData => {
            setTeamInfo(teamData);
            setPageLoading(false);
        })
        .catch((err) => {
          if (err.status === 404) {
            router.push({
                pathname: '/_error',
                query: {
                    statusCode: 404,
                    message: 'The team you are looking for could not be found. It may have been deleted.'
                }
            });
          } else {
             router.push({
                pathname: '/_error',
                query: {
                    statusCode: err.status || 500,
                    message: 'An error occurred while trying to load the team dashboard.'
                }
            });
          }
        });
    }
  }, [teamId, router]);

  useEffect(() => {
    if (router.isReady && teamId) {
      if (generationCompletionEvent) {
          if (String(generationCompletionEvent.teamId) === String(teamId)) {
            setRefreshKey(prev => prev + 1);
            clearGenerationEvent();
        }
      }
    }
  }, [router.isReady, teamId, generationCompletionEvent, clearGenerationEvent]);

  const handleStartTeamGeneration = (preferences: PreferencesCreate) => {
    if (typeof teamId === 'string') {
      startGeneration(preferences, teamId);
    }
  };

  const handleSelectPath = (path: any) => {
    router.push(`/paths/${path.id}?teamId=${teamId}`);
  };


  if (isLoading || pageLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (typeof window !== 'undefined') {
      router.push('/login');
    }
    return null;
  }

  if (!teamId || typeof teamId !== 'string') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Invalid team ID</div>
      </div>
    );
  }

  const isGeneratingForThisTeam = generationState.inProgress && generationState.teamId === teamId;

  return (
    <motion.div
      className="min-h-screen bg-[#f4f7fb]"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.2 } },
      }}
    >
      <motion.div variants={anim.fadeSlide}>
        <TeamDashboard
          teamId={teamId}
          onSelectPath={handleSelectPath}
          isGenerating={isGeneratingForThisTeam}
          startTeamGeneration={handleStartTeamGeneration}
          refreshKey={refreshKey}
        />
      </motion.div>
    </motion.div>
  );
}