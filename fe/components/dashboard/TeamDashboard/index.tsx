"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { teamApi, api } from "@/lib/api";
import type { Team } from "@/types/teams";
import { TeamMemberRole } from "@/types/teams";
import type { LearningPathFE, PreferencesCreate } from "@/types/learning-paths";
import { UserProfile, LearningGoal } from "@/types/user";
import { TeamDashboardProps } from "@/components/dashboard/TeamDashboard/types";
import { teamStyles } from "@/components/dashboard/TeamDashboard/styles";
import { useRouter } from "next/router"
import BackgroundEffects from "@/components/dashboard/TeamDashboard/BackgroundEffects";
import TeamHeader from "@/components/dashboard/TeamDashboard/TeamHeader";
import TeamProgress from "@/components/dashboard/TeamDashboard/TeamProgress";
import LearningPathsList from "@/components/dashboard/TeamDashboard/LearningPathsList";
import TeamModals from "@/components/dashboard/TeamDashboard/TeamModals";
import TeamMembersCard from "@/components/dashboard/TeamDashboard/TeamMembersCard";
import TeamStatisticsDetails from "@/components/dashboard/TeamDashboard/TeamLeadStatistics";
import TeamMemberStatistics from "@/components/dashboard/TeamDashboard/TeamMemberStatistics";


export default function TeamDashboard({ teamId, onSelectPath, isGenerating, startTeamGeneration, refreshKey=0 }: TeamDashboardProps) {  const { user } = useAuth();
  const router = useRouter();
  const [team, setTeam] = useState<Team | null>(null);
  const [paths, setPaths] = useState<any[]>([]);
  const [teamStats, setTeamStats] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [joinCode, setJoinCode] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [showTeamProfileSetup, setShowTeamProfileSetup] = useState(false);
  const [showKickConfirmation, setShowKickConfirmation] = useState(false);
  const [memberToKick, setMemberToKick] = useState<any>(null);
  const [isKicking, setIsKicking] = useState(false);
  const [view, setView] = useState<'paths' | 'stats'>('paths');
  const [showDeletePathModal, setShowDeletePathModal] = useState(false);
  const [pathToDelete, setPathToDelete] = useState<any>(null);
  const [isDeletingPath, setIsDeletingPath] = useState(false);
  const [showDeleteTeamModal, setShowDeleteTeamModal] = useState(false);
  const [isDeletingTeam, setIsDeletingTeam] = useState(false);
  const [deleteTeamNameConfirmation, setDeleteTeamNameConfirmation] = useState("");

  const isTeamLead = team?.members.some(
    (member) => member.user?.id === user?.id && member.role === TeamMemberRole.TEAM_LEAD
  ) || false;

  const fetchTeamData = useCallback(async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      setError(null);
      const [teamData, teamPathsResponse, teamStatistics, userPaths] = await Promise.all([
        teamApi.getTeam(teamId),
        teamApi.getTeamLearningPaths(teamId),
        teamApi.getTeamStatistics(teamId),
        api.getUserLearningPaths(user.id),
      ]);
      const teamPaths = teamPathsResponse || [];
      const userProgressMap = new Map(userPaths.map((p: LearningPathFE) => [p.id, p.completion_percentage]));
      const mergedPaths = teamPaths.map((teamPath: any) => ({
        ...teamPath,
        progress: userProgressMap.get(teamPath.id) || 0,
      }));
      setTeam(teamData);
      setPaths(mergedPaths);
      setTeamStats(teamStatistics);
    } catch (err) {
      setError("Failed to load team data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [user?.id, teamId]);

  const generateInviteCode = async () => {
    try {
      const response = await teamApi.generateJoinCode(teamId);
      setJoinCode(response.join_code);
      setShowInviteModal(true);
    } catch (error) {
      alert("Failed to generate invite code. Please try again.");
    }
  };

  const copyJoinCode = async () => {
    try {
      await navigator.clipboard.writeText(joinCode);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      alert("Failed to copy join code. Please copy it manually.");
    }
  };

  const openManageModal = async () => {
    setShowManageModal(true);
    setLoadingMembers(true);
    try {
      const members = await teamApi.getTeamMembers(teamId);
      setTeamMembers(members);
    } catch (error) {
      alert("Failed to load team members. Please try again.");
    } finally {
      setLoadingMembers(false);
    }
  };

  const kickMember = (member: any) => {
    setMemberToKick(member);
    setShowKickConfirmation(true);
  };

  const confirmKickMember = async () => {
    if (!memberToKick) return;
    setIsKicking(true);
    try {
      await teamApi.removeTeamMember(teamId, memberToKick.user.id);
      setTeamMembers(prev => prev.filter(m => m.id !== memberToKick.id));
      setTeam(prev => prev ? { ...prev, members: prev.members.filter(m => m.id !== memberToKick.id) } : null);
      setShowKickConfirmation(false);
      setMemberToKick(null);
    } catch (error) {
      alert("Failed to remove team member. Please try again.");
    } finally {
      setIsKicking(false);
    }
  };

  function mapLearningStyleForAPI(style: string): "visual" | "auditory" | "kinesthetic" | "reading-writing" {
    switch (style) {
      case "visual": case "auditory": case "kinesthetic": return style;
      case "reading": return "reading-writing";
      default: return "visual";
    }
  }

  const handleProfileSetupComplete = async (profile: UserProfile, goal: LearningGoal) => {
    const preferences: PreferencesCreate = {
      subject: goal.goal || "General Learning",
      experience_level: (profile.experience_level as "beginner" | "intermediate" | "advanced") || "beginner",
      learning_styles: Array.isArray(profile.learning_styles) && profile.learning_styles.length > 0
        ? profile.learning_styles.map(mapLearningStyleForAPI)
        : [mapLearningStyleForAPI(profile.learning_styles?.[0] || "visual")],
      preferred_platforms: profile.platforms || ["YouTube", "Coursera"],
      study_time_minutes: profile.available_time || 60,
      goals: goal.goal || "Learn new skills",
    };
    setShowTeamProfileSetup(false);
    startTeamGeneration(preferences);
  };

  // --- DELETE HANDLERS ---
  const handleDeletePath = (path: any) => {
    setPathToDelete(path);
    setShowDeletePathModal(true);
  };

  const confirmDeletePath = async () => {
    if (!pathToDelete) return;
    setIsDeletingPath(true);
    try {
      await api.deleteLearningPath(pathToDelete.id);
      await fetchTeamData(); // Refresh paths after deletion
      setPaths(prev => prev.filter(p => p.id !== pathToDelete.id));
      setShowDeletePathModal(false);
      setPathToDelete(null);
    } catch (err) {
      alert("Failed to delete the learning path. Please try again.");
    } finally {
      setIsDeletingPath(false);
    }
  };
  
  const handleDeleteTeam = () => {
    setShowManageModal(false); // Close manage modal before opening delete modal
    setShowDeleteTeamModal(true);
  };

  const confirmDeleteTeam = async () => {
    if (!team || deleteTeamNameConfirmation !== team.name) {
      alert("The entered name does not match the team name.");
      return;
    }
    setIsDeletingTeam(true);
    try {
      await teamApi.deleteTeam(teamId);
      router.push('/dashboard');
    } catch (err) {
      alert("Failed to delete the team. Please try again.");
      setIsDeletingTeam(false);
    }
  };

  useEffect(() => {
    if (user?.id && teamId) {
      fetchTeamData();
    }
  }, [user?.id, teamId, fetchTeamData]);

  useEffect(() => {
    if (refreshKey > 0) {
      fetchTeamData();
    }
  }, [refreshKey, fetchTeamData]);

  if (loading && !team) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-purple-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#5E35B1] mx-auto mb-4"></div>
          <p className="text-[#380A63]/70 text-lg">Loading team dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-purple-100">
        <div className="text-center">
          <div className="p-4 rounded-2xl bg-red-100 text-red-600 w-fit mx-auto mb-4">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <h3 className="text-xl font-semibold text-[#380A63] mb-2">Oops! Something went wrong</h3>
          <p className="text-[#380A63]/70 mb-6">{error}</p>
          <button onClick={fetchTeamData} className="px-6 py-3 bg-gradient-to-r from-[#5E35B1] to-[#380A63] text-white rounded-lg font-semibold hover:shadow-lg transition-shadow duration-200">
            Try Again
          </button>
        </div>
      </div>
    );
  }
  const activePathsCount = teamStats?.total_paths || paths.length;
  const memberCount = teamStats?.total_members ?? team?.members.length ?? 0;
  const avgProgress = Math.round(teamStats?.avg_progress_percentage || 0);

  return (
    <div className={teamStyles.container}>
      <BackgroundEffects />
      <div className={teamStyles.wrapper}>
        <div className={teamStyles.leftCol}>
          <TeamHeader
            team={team}
            isTeamLead={isTeamLead}
            onGenerateInviteCode={generateInviteCode}
            onOpenManageModal={openManageModal}
            pathsCount={paths.length}
            view={view}
            onViewChange={setView}
          />

         <div className="mt-8">
            {view === 'paths' ? (
              <LearningPathsList
                paths={paths}
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
                onSelectPath={onSelectPath}
                onShowTeamProfileSetup={() => setShowTeamProfileSetup(true)}
                isTeamLead={isTeamLead}
                isGenerating={isGenerating}
                onDeletePath={handleDeletePath}
              />
            ) : (
              <>
                {isTeamLead && (
                  <TeamStatisticsDetails teamId={teamId} />
                )}
                {!isTeamLead && (
                  <TeamMemberStatistics teamId={teamId} />
                )}
              </>
            )}
          </div>
        </div>
        <div className={teamStyles.rightCol}>
          <TeamProgress
            activePaths={activePathsCount}
            memberCount={memberCount}
            avgProgress={avgProgress}
          />
          <TeamMembersCard team={team} />
        </div>
      </div>
      <TeamModals
        showInviteModal={showInviteModal}
        onCloseInviteModal={() => setShowInviteModal(false)}
        joinCode={joinCode}
        copySuccess={copySuccess}
        onCopyJoinCode={copyJoinCode}
        showManageModal={showManageModal}
        onCloseManageModal={() => setShowManageModal(false)}
        teamMembers={teamMembers}
        loadingMembers={loadingMembers}
        isTeamLead={isTeamLead}
        onKickMember={kickMember}
        showTeamProfileSetup={showTeamProfileSetup}
        onCloseTeamProfileSetup={() => setShowTeamProfileSetup(false)}
        onProfileSetupComplete={handleProfileSetupComplete}
        user={user}
        showKickConfirmation={showKickConfirmation}
        onCloseKickConfirmation={() => setShowKickConfirmation(false)}
        memberToKick={memberToKick}
        isKicking={isKicking}
        onConfirmKickMember={confirmKickMember}
        showDeletePathModal={showDeletePathModal}
        onCloseDeletePathModal={() => setShowDeletePathModal(false)}
        pathToDelete={pathToDelete}
        isDeletingPath={isDeletingPath}
        onConfirmDeletePath={confirmDeletePath}
        onDeleteTeam={handleDeleteTeam}
        showDeleteTeamModal={showDeleteTeamModal}
        onCloseDeleteTeamModal={() => setShowDeleteTeamModal(false)}
        teamToDelete={team}
        isDeletingTeam={isDeletingTeam}
        onConfirmDeleteTeam={confirmDeleteTeam}
        deleteTeamNameConfirmation={deleteTeamNameConfirmation}
        setDeleteTeamNameConfirmation={setDeleteTeamNameConfirmation}
      />
    </div>
  );
}