import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from 'next/router';
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { NotificationProvider, useNotifications } from "@/context/NotificationContext";
import { ChatProvider } from '@/context/ChatContext';
import { useLearningPathGenerator } from '@/hooks/custom/useLearningPathGenerator';
import Header from "@/components/common/Header";
import Footer from "@/components/common/Footer";
import TeamSidebar from "@/components/dashboard/TeamSidebar";
import { IntegratedChatAssistant } from '@/components/chat/IntegratedChatAssistant';

function AppLayout({ Component, pageProps }: { Component: AppProps['Component']; pageProps: AppProps['pageProps'] }) {
  const { user } = useAuth();
  const { selectionEvent, clearSelection } = useNotifications();
  const router = useRouter();

  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState<'personal' | string>('personal');
  const [, setCurrentTeamId] = useState<string | null>(null);

  useEffect(() => {
    const { teamId } = router.query;
    if (router.pathname.startsWith('/teams/') && typeof teamId === 'string') {
      setCurrentTeamId(teamId);
      setCurrentView(teamId);
    } else if (router.pathname === '/dashboard' || router.pathname === '/') {
      setCurrentTeamId(null);
      setCurrentView('personal');
    }
  }, [router.pathname, router.query]);

  const {
    isGenerating,
    generatedPathId,
    currentStatus,
    startGeneration,
    resetGeneration,
    generationContext,
  } = useLearningPathGenerator({
    userId: user?.id,
  });

  const noLayoutPages = ['/login', '/auth/verify', '/about'];
  const showLayout = !noLayoutPages.includes(router.pathname);

  useEffect(() => {
    if (selectionEvent) {
      const { pathId, teamId } = selectionEvent;
      const redirectUrl = teamId ? `/paths/${pathId}?teamId=${teamId}` : `/paths/${pathId}`;
      router.push(redirectUrl);
      clearSelection();
    }
  }, [selectionEvent, router, clearSelection]);

  const handleToggleSidebar = () => setSidebarOpen(prev => !prev);
  const handleCloseSidebar = () => setSidebarOpen(false);

  const handleViewChange = (view: 'personal' | string) => {
    if (view === 'personal') {
      router.push('/dashboard');
    } else {
      router.push(`/teams/${view}`);
    }
    setCurrentView(view);
    handleCloseSidebar();
  };

  const enhancedPageProps = {
    ...pageProps,
    generationState: {
      inProgress: isGenerating,
      teamId: generationContext.teamId,
      taskId: generationContext.taskId,
      generatedPathId: generatedPathId,
      currentStatus: currentStatus,
    },
    startGeneration: startGeneration,
    resetGeneration: resetGeneration,
  };

  if (!showLayout) {
    return <Component {...enhancedPageProps} />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        username={user?.username || user?.email || ''}
        onOpenSidebar={handleToggleSidebar}
      />
      <div className="flex flex-1">
        <TeamSidebar
          isOpen={isSidebarOpen}
          onClose={handleCloseSidebar}
          currentView={currentView}
          onViewChange={handleViewChange}
        />
        <main className="flex-1">
          <Component {...enhancedPageProps} />
        </main>
      </div>
      <Footer />
      <ChatAssistantWithUserId />
    </div>
  );
}

function ChatAssistantWithUserId() {
  const { user } = useAuth();
  if (!user) return null;
  return <IntegratedChatAssistant userId={user.id} />;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <NotificationProvider>
        <ChatProvider initialLocation="dashboard">
          <Head>
            <link rel="icon" href="/favicon.png" />
            <title>Skill Central</title>
          </Head>
          <AppLayout Component={Component} pageProps={pageProps} />
        </ChatProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}