import { motion } from "framer-motion";
import { Crown } from "lucide-react";
import { teamStyles } from "@/components/dashboard/TeamDashboard/styles";
import { TeamMemberRole } from "@/types/teams";
import { TeamMembersCardProps } from "@/components/dashboard/TeamDashboard/types";

// Get initials from a name
const getInitials = (name: string): string => {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
};

export default function TeamMembersCard({ team }: TeamMembersCardProps) {
  if (!team || !team.members) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className={teamStyles.sidebarCard}
    >
      <h3 className="text-xl font-bold bg-gradient-to-r from-[#380A63] to-[#5E35B1] bg-clip-text text-transparent mb-4">
        Team Members
      </h3>
      <div className="space-y-3 max-h-96 overflow-y-auto overflow-x-hidden p-2">
        {team.members.map((member) => (
          <div
            key={member.user_id}
            className="flex items-center justify-between p-3 bg-gradient-to-r from-[#380A63]/5 to-[#5E35B1]/10 rounded-xl hover:scale-105 transition-transform duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-xl flex items-center justify-center shadow-sm">
                <span className="text-sm font-bold text-white">
                  {getInitials(member.user?.full_name || member.user?.username || "")}
                </span>
              </div>
              <div>
                <p className="font-semibold text-black">
                  {member.user?.full_name || member.user?.username}
                </p>
                <p className="text-xs text-black/80 capitalize">
                  {member.role === TeamMemberRole.TEAM_LEAD ? "Team Lead" : "Member"}
                </p>
              </div>
            </div>
            {member.role === TeamMemberRole.TEAM_LEAD && (
              <Crown className="w-5 h-5 text-amber-500" />
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}
