import { PreferencesCreate } from "@/types/learning-paths";
import type {Team} from "@/types/teams";

export interface TeamDashboardProps {
  teamId: string;
  onSelectPath?: (path: any) => void;
  isGenerating: boolean;
  startTeamGeneration: (preferences: PreferencesCreate) => void;
  refreshKey?: number;
}

export interface TeamHeaderProps {
  team: Team | null;
  isTeamLead: boolean;
  onGenerateInviteCode: () => void;
  onOpenManageModal: () => void;
  pathsCount: number;
  view: 'paths' | 'stats';
  onViewChange: (view: 'paths' | 'stats') => void;
}

export interface TeamMembersCardProps {
  team: Team | null;
}

export interface TeamProgressProps {
  activePaths: number;
  memberCount: number;
  avgProgress: number;
}

export interface LearningPathsListProps {
  paths: any[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  onSelectPath?: (path: any) => void;
  onShowTeamProfileSetup: () => void;
  isTeamLead: boolean;
  isGenerating: boolean;
  onDeletePath: (path: any) => void; // Add this prop
}

export interface TeamModalsProps {
  // Invite Modal
  showInviteModal: boolean;
  onCloseInviteModal: () => void;
  joinCode: string;
  copySuccess: boolean;
  onCopyJoinCode: () => void;
  
  // Manage Modal
  showManageModal: boolean;
  onCloseManageModal: () => void;
  teamMembers: any[];
  loadingMembers: boolean;
  isTeamLead: boolean;
  onKickMember: (member: any) => void;
  
  // Profile Setup Modal
  showTeamProfileSetup: boolean;
  onCloseTeamProfileSetup: () => void;
  onProfileSetupComplete: (profile: any, goal: any) => void;
  user: any;
  
  // Kick Confirmation Modal
  showKickConfirmation: boolean;
  onCloseKickConfirmation: () => void;
  memberToKick: any;
  isKicking: boolean;
  onConfirmKickMember: () => void;

  // Delete Path Confirmation Modal
  showDeletePathModal: boolean;
  onCloseDeletePathModal: () => void;
  pathToDelete: any;
  isDeletingPath: boolean;
  onConfirmDeletePath: () => void;

  // Delete Team Confirmation Modal
  onDeleteTeam: () => void;
  showDeleteTeamModal: boolean;
  onCloseDeleteTeamModal: () => void;
  teamToDelete: any;
  isDeletingTeam: boolean;
  onConfirmDeleteTeam: () => void;
  deleteTeamNameConfirmation: string;
  setDeleteTeamNameConfirmation: (name: string) => void;
}