"use client";

import { useState, useEffect, useRef, RefObject } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  Home,
  Plus,
  ChevronRight,
  UserPlus,
  Crown,
  X,
  AlertCircle,
  LogIn,
  Info,
} from "lucide-react";
import { Button } from "@/components/common/Button";
import { teamApi } from "@/lib/api";
import type { Team } from "@/types/teams";
import { useAuth } from "@/context/AuthContext";
import { useOnClickOutside } from "@/hooks/useOnClickOutside";

interface TeamSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentView: "personal" | string;
  onViewChange: (view: "personal" | string) => void;
}

export default function TeamSidebar({ isOpen, onClose, currentView, onViewChange }: TeamSidebarProps) {
  const { user } = useAuth();
  const sidebarRef = useRef<HTMLDivElement>(null);
  useOnClickOutside(sidebarRef as RefObject<HTMLDivElement>, () => {
    if (isOpen) onClose();
  });

  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  const [notification, setNotification] = useState<{ title: string; message: string } | null>(null);

  // Modal states
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinCode, setJoinCode] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [joinError, setJoinError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    if (isOpen && user) {
      fetchMyTeams();
    }
  }, [isOpen, user]);

  const fetchMyTeams = async () => {
    try {
      setLoading(true);
      const myTeams = await teamApi.getMyTeams();
      setTeams(myTeams);
    } catch (error) {}
    finally {
      setLoading(false);
    }
  };

  const handleCreateTeam = async () => {
  if (isCreating) return;

  if (!newTeamName.trim()) {
    setCreateError("Please enter a name for your team.");
    return;
  }

  setIsCreating(true);
  setCreateError("");
  try {
    const newTeam = await teamApi.createTeam({ name: newTeamName.trim() });
    setShowCreateModal(false);
    setNewTeamName("");
    fetchMyTeams();
    setNotification({
      title: `Team '${newTeam.name}' Created`,
      message: "You can now invite members and start collaborating."
    });
    setTimeout(() => setNotification(null), 4000);
  } catch (error: any) {
    if (error.message?.includes("Team name already exists")) {
      setCreateError("A team with this name already exists. Please choose a different one.");
    } else {
      setCreateError("Failed to create team due to an unexpected error. Please try again.");
    }
  } finally {
    setIsCreating(false);
  }
};

  const handleJoinTeam = async () => {
  if (isJoining) return;

  const trimmedCode = joinCode.trim();

  if (trimmedCode === "") {
    setJoinError("Please enter an invitation code.");
    return;
  }
  if (trimmedCode.length !== 6) {
    setJoinError("The invitation code must be 6 characters long.");
    return;
  }

  setIsJoining(true);
  setJoinError("");
  try {
    await teamApi.joinTeamByCode({ join_code: trimmedCode });
    setShowJoinModal(false);
    setJoinCode("");
    fetchMyTeams();
    setNotification({
        title: "Success",
        message: "You have successfully joined the team."
    });
    setTimeout(() => setNotification(null), 4000);
  } catch (error: any) {
    setJoinError(error.message || "Failed to join team. The code might be invalid or expired.");
  } finally {
    setIsJoining(false);
  }
};

  const getTeamColor = (teamId: string) => {
    const colors = [
      "from-teal-400 to-cyan-500",
      "from-orange-400 to-red-500",
      "from-blue-500 to-indigo-600",
      "from-green-400 to-emerald-500",
      "from-purple-500 to-pink-500",
    ];
    const index = teamId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
  };

  const isCurrentUserTeamLead = (team: Team) => {
    return team.team_lead_id === user?.id;
  };

  return (
    <>
      <AnimatePresence>
        {notification && (
          <motion.div
            layout
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed top-6 right-6 z-50 w-full max-w-sm"
          >
            <div className="bg-sky-50 border-l-4 border-sky-400 text-sky-800 p-4 rounded-lg shadow-xl" role="alert">
                <div className="flex items-center">
                    <Info className="h-6 w-6 text-sky-500 mr-3 flex-shrink-0" />
                    <div className="flex-grow">
                        <p className="font-bold text-sky-900">{notification.title}</p>
                        <p className="text-sm">{notification.message}</p>
                    </div>
                </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
           <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 z-40"
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
            <motion.div
              ref={sidebarRef}
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 w-72 bg-white border-r border-gray-200 shadow-2xl z-50 flex flex-col"
            >
              <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
                <h2 className="text-xl font-semibold text-gray-900">Workspaces</h2>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={onClose}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </motion.button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <motion.button
                  onClick={() => onViewChange("personal")}
                  className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 ${
                    currentView === "personal"
                      ? "bg-purple-50 text-purple-700 border border-purple-200 shadow-sm"
                      : "hover:bg-gray-100 text-gray-700"
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className={`p-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500`}>
                    <Home className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-semibold">Personal Dashboard</span>
                </motion.button>

                <div className="pt-2">
                  <div className="flex items-center justify-between mb-2 px-2">
                    <h3 className="text-md font-bold text-neutral-secondary-light uppercase tracking-wider">Teams</h3>
                    <div className="flex items-center gap-1">
                      {/* Join Button */}
                      <div className="relative group">
                        <Button
                          variant="hollow"
                          onClick={() => setShowJoinModal(true)}
                          className="p-1.5 rounded-md"
                          aria-label="Join Team"
                        >
                          <UserPlus className="w-4 h-4" />
                        </Button>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-2 py-1 bg-gray-800 text-white text-xs font-semibold rounded-md opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all pointer-events-none">
                          Join Team
                        </div>
                      </div>
                      {/* Create Button */}
                      <div className="relative group">
                        <Button
                          variant="primary"
                          onClick={() => setShowCreateModal(true)}
                          className="p-1.5 rounded-md"
                          aria-label="Create Team"
                        >
                          <Plus className="w-4 h-4" strokeWidth={3} />
                        </Button>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-2 py-1 bg-gray-800 text-white text-xs font-semibold rounded-md opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all pointer-events-none">
                          Create Team
                        </div>
                      </div>
                    </div>
                  </div>

                  {loading ? (
                    <div className="space-y-2 mt-2">
                      {[1, 2].map((i) => (
                        <div key={i} className="animate-pulse flex items-center space-x-3 p-3">
                            <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                            <div className="flex-1 space-y-2">
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                            </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {teams.map((team) => (
                        <motion.button
                          key={team.id}
                          onClick={() => onViewChange(team.id)}
                          className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 ${
                            currentView === team.id
                              ? "bg-purple-50 text-purple-700 border border-purple-200 "
                              : "hover:bg-gray-100 text-gray-700 shadow-sm"
                          }`}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <div className={`p-2 rounded-lg bg-gradient-to-r ${getTeamColor(team.id)}`}>
                            <Users className="w-5 h-5 text-white" />
                          </div>
                          <div className="flex-1 text-left min-w-0">
                            <div className="flex items-center space-x-1.5">
                              <span className="font-bold truncate">{team.name}</span>
                              {isCurrentUserTeamLead(team) && (
                                <Crown className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-gray-500">
                              {team.members.length} member{team.members.length !== 1 ? 's' : ''}
                            </p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        </motion.button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showJoinModal && (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
            onClick={() => setShowJoinModal(false)}
        >
            <motion.div
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md border border-gray-200/80"
            >
                <div className="flex flex-col items-center text-center mb-6">
                    <div className="w-14 h-14 rounded-full bg-violet-100 flex items-center justify-center mb-4 border-4 border-violet-50">
                        <LogIn className="w-8 h-8 text-violet-600" />
                    </div>
                    <h3 className="text-xl font-bold font-display text-neutral-dark">Join an Existing Team</h3>
                    <p className="text-md text-neutral mt-1">Enter the invitation code you received.</p>
                </div>

                <div className="space-y-2">
                    <div>
                        <label htmlFor="joinCode" className="text-md font-bold text-neutral mb-1 block">
                            Invitation Code
                        </label>
                        <input
                            id="joinCode"
                            type="text"
                            value={joinCode}
                            onChange={(e) => {
                                const value = e.target.value.toUpperCase().trim();
                                setJoinCode(value);
                                setJoinError("");
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    e.preventDefault();
                                    handleJoinTeam();
                                }
                            }}
                            placeholder="Enter 6-character code"
                            maxLength={6}
                            className={`w-full px-4 py-2 bg-gray-50 border rounded-lg
                                   focus:ring-2 focus:border-violet-500
                                   transition-all duration-200 text-md ${joinError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-violet-500'}`}
                        />
                    </div>
                    {joinError && (
                        <div className="flex items-center text-sm text-red-600 bg-red-50 p-3 rounded-lg">
                            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                            <span>{joinError}</span>
                        </div>
                    )}
                    <div className="flex justify-end space-x-3 pt-4 text-md">
                        <Button variant="hollow" onClick={() => setShowJoinModal(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleJoinTeam}
                            disabled={isJoining}
                        >
                            {isJoining ? "Joining..." : "Join Team"}
                        </Button>
                    </div>
                </div>
            </motion.div>
        </motion.div>
      )}
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md border border-gray-200/80"
            >
              <div className="flex flex-col items-center text-center mb-6">
                <div className="w-14 h-14 rounded-full bg-violet-100 flex items-center justify-center mb-4 border-4 border-violet-50">
                  <Users className="w-8 h-8 text-violet-600" />
                </div>
                <h3 className="text-xl font-bold font-display text-neutral-dark">Create a New Team</h3>
                <p className="text-md text-neutral mt-1">Give your team a name to get started.</p>
              </div>
              <div className="space-y-2">
                <div>
                  <label htmlFor="teamName" className="text-md font-bold text-neutral mb-1 block">
                    Team Name
                  </label>
                  <input
                    id="teamName"
                    type="text"
                    value={newTeamName}
                    onChange={(e) => {
                      setNewTeamName(e.target.value);
                      setCreateError("");
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleCreateTeam();
                      }
                    }}
                    placeholder="e.g., Marketing Squad, Project Phoenix"
                    className={`w-full px-4 py-2 bg-gray-50 border rounded-lg
                               focus:ring-2 focus:border-violet-500
                               transition-all duration-200 text-md ${createError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-violet-500'}`}
                  />
                </div>
                {createError && (
                  <div className="flex items-center text-sm text-red-600 bg-red-50 p-3 rounded-lg">
                    <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                    <span>{createError}</span>
                  </div>
                )}
                <div className="flex justify-end space-x-3 pt-4 text-md">
                  <Button variant="hollow" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateTeam}
                    disabled={isCreating}
                  >
                    {isCreating ? "Creating..." : "Create Team"}
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}