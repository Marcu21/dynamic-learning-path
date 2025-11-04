import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, Crown, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/common/Button";
import ProfileSetup from "@/components/learning-path/ProfileSetup";
import { TeamMemberRole } from "@/types/teams";
import { TeamModalsProps } from "./types";

export default function TeamModals({
  // Invite Modal
  showInviteModal,
  onCloseInviteModal,
  joinCode,
  copySuccess,
  onCopyJoinCode,
  
  // Manage Modal
  showManageModal,
  onCloseManageModal,
  teamMembers,
  loadingMembers,
  isTeamLead,
  onKickMember,
  
  // Profile Setup Modal
  showTeamProfileSetup,
  onCloseTeamProfileSetup,
  onProfileSetupComplete,
  user,
  
  // Kick Confirmation Modal
  showKickConfirmation,
  onCloseKickConfirmation,
  memberToKick,
  isKicking,
  onConfirmKickMember,

  // Delete Path Modal
  showDeletePathModal,
  onCloseDeletePathModal,
  pathToDelete,
  isDeletingPath,
  onConfirmDeletePath,

  // Delete Team Modal
  onDeleteTeam,
  showDeleteTeamModal,
  onCloseDeleteTeamModal,
  teamToDelete,
  isDeletingTeam,
  onConfirmDeleteTeam,
  deleteTeamNameConfirmation,
  setDeleteTeamNameConfirmation,
}: TeamModalsProps) {
  return (
    <>
      {/* Invite Modal */}
      <AnimatePresence>
        {showInviteModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
            transition={{ duration: 0.2, ease: "easeOut" }}

              className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
            >
              <h3 className="text-2xl font-bold bg-gradient-to-r from-[#380A63] to-[#5E35B1] bg-clip-text text-transparent mb-6">
                Invite Team Members
              </h3>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-[#380A63]/70 mb-2">
                  Share this join code:
                </label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 p-3 bg-[#380A63]/5 rounded-lg border border-[#380A63]/20 font-mono text-lg">
                    {joinCode}
                  </div>
                  <Button
                    onClick={onCopyJoinCode}
                    className="px-3 py-3 bg-[#5E35B1] hover:bg-[#380A63] text-white rounded-lg transition-colors duration-200"
                  >
                    {copySuccess ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  onClick={onCloseInviteModal}
                  variant="hollow"
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Manage Team Modal */}
      <AnimatePresence>
        {showManageModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl"
            >
              <h3 className="text-2xl font-bold bg-gradient-to-r from-[#380A63] to-[#5E35B1] bg-clip-text text-transparent mb-6 flex-shrink-0">
                Manage Team
              </h3>
              
              <div className="flex-grow overflow-y-auto pr-2">
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-[#380A63] mb-4">Team Members</h4>
                  
                  {loadingMembers ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5E35B1] mx-auto"></div>
                      <p className="text-[#380A63]/60 mt-2">Loading members...</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {teamMembers.map((member) => (
                        <div key={member.id} className="flex items-center justify-between p-4 bg-[#380A63]/5 rounded-xl border border-[#380A63]/10">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-xl flex items-center justify-center shadow-md">
                              <span className="text-sm font-bold text-white">
                                {(member.user?.full_name || member.user?.username || 'U')[0].toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="font-semibold text-[#380A63]">
                                {member.user?.full_name || member.user?.username || 'Unknown User'}
                              </p>
                              <div className="flex items-center space-x-2 text-sm text-[#380A63]/60">
                                <span>@{member.user?.username || 'unknown'}</span>
                                {member.role === TeamMemberRole.TEAM_LEAD && (
                                  <div className="flex items-center space-x-1 text-amber-600">
                                    <Crown className="w-3 h-3" />
                                    <span>Lead</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {isTeamLead && member.role !== TeamMemberRole.TEAM_LEAD && (
                            <Button
                              onClick={() => onKickMember(member)}
                              variant="hollow"
                              className="text-red-600 border-red-200 hover:bg-red-50"
                            >
                              Kick
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* MODIFICATION: Danger Zone Section */}
                {isTeamLead && (
                  <div className="mt-8 pt-6 border-t border-dashed border-red-300">
                      <h4 className="text-lg font-semibold text-red-700 mb-4">Danger Zone</h4>
                      <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-xl">
                          <div>
                              <p className="font-semibold text-red-800">Delete this team</p>
                              <p className="text-sm text-red-600">Once deleted, it's gone forever. Please be certain.</p>
                          </div>
                          <Button 
                              onClick={onDeleteTeam} 
                              variant="alert"
                              className="bg-red-600 hover:bg-red-700"
                          >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete Team
                          </Button>
                      </div>
                  </div>
                )}
              </div>
              
              <div className="flex justify-end space-x-3 flex-shrink-0 pt-6">
                <Button
                  onClick={onCloseManageModal}
                  variant="hollow"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Team ProfileSetup Modal for Path Creation */}
      <AnimatePresence>
        {showTeamProfileSetup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
              <ProfileSetup
                onComplete={onProfileSetupComplete}
                onCancel={onCloseTeamProfileSetup}
                username={user?.username}
                theme="team"
              />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Kick Confirmation Modal */}
      <AnimatePresence>
        {showKickConfirmation && memberToKick && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
            >
              <h3 className="text-2xl font-bold bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent mb-4">
                Remove Team Member
              </h3>
              
              <div className="mb-6">
                <div className="flex items-center justify-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-xl flex items-center justify-center shadow-md">
                    <span className="text-lg font-bold text-white">
                      {(memberToKick.user?.full_name || memberToKick.user?.username || 'U')[0].toUpperCase()}
                    </span>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-[#380A63] text-lg">
                      {memberToKick.user?.full_name || memberToKick.user?.username || 'Unknown User'}
                    </p>
                    <p className="text-sm text-[#380A63]/70">
                      @{memberToKick.user?.username || 'unknown'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
                <p className="text-sm text-red-800 mb-3 font-semibold">
                  ⚠️ This action cannot be undone.
                </p>
                <p className="text-sm text-red-700">
                  This member will be removed from the team and their progress on all team learning paths will be permanently deleted.
                </p>
              </div>
              
              <div className="flex space-x-3">
                <Button
                  onClick={onCloseKickConfirmation}
                  disabled={isKicking}
                  variant="hollow"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={onConfirmKickMember}
                  disabled={isKicking}
                  variant="alert"
                  className="flex-1 bg-green"
                >
                  {isKicking ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Removing...
                    </>
                  ) : (
                    "Remove Member"
                  )}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Path Confirmation Modal */}
      <AnimatePresence>
        {showDeletePathModal && pathToDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-800">Delete Learning Path</h3>
              </div>
              <p className="text-gray-600 mb-6">
                Are you sure you want to permanently delete the learning path "<strong>{pathToDelete.title}</strong>"? This action cannot be undone.
              </p>
              <div className="flex space-x-3">
                <Button onClick={onCloseDeletePathModal} disabled={isDeletingPath} variant="hollow" className="flex-1">
                  Cancel
                </Button>
                <Button onClick={onConfirmDeletePath} disabled={isDeletingPath} variant="alert" className="flex-1">
                  {isDeletingPath ? "Deleting..." : "Delete Path"}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Team Confirmation Modal */}
      <AnimatePresence>
        {showDeleteTeamModal && teamToDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="bg-white rounded-2xl p-8 max-w-lg w-full shadow-2xl"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-2xl font-bold text-red-700">Delete Team</h3>
              </div>
              <div className="space-y-4 text-gray-700">
                <p>This is a highly destructive action. You are about to delete the entire team "<strong>{teamToDelete.name}</strong>".</p>
                <ul className="list-disc list-inside space-y-2 bg-red-50 p-4 rounded-lg border border-red-200">
                  <li>All team learning paths will be permanently deleted.</li>
                  <li>All team member progress will be lost.</li>
                  <li>All members will be removed from the team.</li>
                </ul>
                <p>To confirm this action, please type the name of the team below:</p>
                <input
                  type="text"
                  value={deleteTeamNameConfirmation}
                  onChange={(e) => setDeleteTeamNameConfirmation(e.target.value)}
                  placeholder={teamToDelete.name}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-red-500"
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <Button onClick={onCloseDeleteTeamModal} disabled={isDeletingTeam} variant="hollow" className="flex-1">
                  Cancel
                </Button>
                <Button
                  onClick={onConfirmDeleteTeam}
                  disabled={isDeletingTeam || deleteTeamNameConfirmation !== teamToDelete.name}
                  variant="alert"
                  className="flex-1"
                >
                  {isDeletingTeam ? "Deleting Team..." : "I understand, delete this team"}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}