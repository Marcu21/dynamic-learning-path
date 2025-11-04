import { motion } from "framer-motion";
import { Users, UserPlus, Settings, LayoutGrid, BarChart3, UserCheck } from "lucide-react";
import { Button } from "@/components/common/Button";
import { teamStyles } from "@/components/dashboard/TeamDashboard/styles";
import { TeamHeaderProps } from "@/components/dashboard/TeamDashboard/types";

export default function TeamHeader({
  team,
  isTeamLead,
  onGenerateInviteCode,
  onOpenManageModal,
  view,
  onViewChange,
}: TeamHeaderProps) {
  const tabs = isTeamLead ? [
    { id: 'paths', label: 'Learning Paths', icon: LayoutGrid },
    { id: 'stats', label: 'Team Statistics', icon: BarChart3 }
  ] : [
    { id: 'paths', label: 'Learning Paths', icon: LayoutGrid },
    { id: 'stats', label: 'My Statistics', icon: UserCheck }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={teamStyles.headerCard}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="p-4 rounded-2xl bg-gradient-to-br from-[#5E35B1] to-[#380A63] shadow-lg">
            <Users className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-[#380A63] via-[#5E35B1] to-[#8E44AD] bg-clip-text text-transparent">
              {team?.name}
            </h1>
            <p className="text-neutral-dark text-lg">{team?.description || "Team learning workspace"}</p>
          </div>
        </div>

        {isTeamLead && (
          <div className="flex items-center space-x-3">
            <Button
              onClick={onGenerateInviteCode}
              className={teamStyles.primaryButton}
            >
              <UserPlus className="w-4 h-4 mr-2" />
              Invite
            </Button>
            <Button
              onClick={onOpenManageModal}
              className={teamStyles.primaryButton}
            >
              <Settings className="w-4 h-4 mr-2" />
              Manage
            </Button>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-purple-200/50">
        <div className="p-1.5 bg-purple-100/70 rounded-xl flex space-x-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => onViewChange(tab.id as 'paths' | 'stats')}
              className={`w-full relative rounded-lg px-4 py-2 text-md font-semibold transition-colors flex items-center justify-center gap-2 ${
                view === tab.id ? 'text-white' : 'text-[#68388F] hover:bg-white/50'
              }`}
            >
              {view === tab.id && (
                <motion.div
                  layoutId="active-view-indicator"
                  className="absolute inset-0 bg-gradient-to-r from-[#5E35B1] to-[#380A63] rounded-lg z-0"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}