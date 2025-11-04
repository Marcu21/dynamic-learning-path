import { motion } from "framer-motion";
import { Target, Users, Trophy} from "lucide-react";
import { teamStyles } from "./styles";
import { TeamProgressProps } from "./types";

export default function TeamProgress({ activePaths, memberCount, avgProgress }: TeamProgressProps) {
  const stats = [
    {
      label: "Total Paths",
      value: activePaths,
      icon: Target,
      style: teamStyles.statIcon,
    },
    {
      label: "Team Members",
      value: memberCount,
      icon: Users,
      style: teamStyles.statIconSubtle,
    },
    {
      label: "Avg. Progress",
      value: `${avgProgress}%`,
      icon: Trophy,
      style: teamStyles.statIconAccent,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
      className={teamStyles.sidebarCard}
    >
      <h3 className="text-xl font-bold bg-gradient-to-r from-[#380A63] to-[#5E35B1] bg-clip-text text-transparent mb-4">
        Team Progress
      </h3>
      <div className="space-y-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="flex items-center space-x-4 p-3 bg-gradient-to-r from-[#380A63]/5 to-[#5E35B1]/10 rounded-xl hover:scale-105 transition-transform duration-200"
            >
              <div className={stat.style}>
                <Icon className="w-6 h-6" />
              </div>
              <div className="flex-1 flex justify-between items-center">
                <p className="text-md font-semibold text-black">{stat.label}</p>
                <p className="text-xl font-bold text-purple-800">{stat.value}</p>
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
