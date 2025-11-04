import React, {useEffect, useState} from 'react';
import { motion, Variants } from 'framer-motion';
import { Award, BarChart, BrainCircuit, Check, Clock, Hourglass, User, Users } from 'lucide-react';
import {CurrentUserStatistics, PersonalTeamStatisticsApiResponse} from "@/types/team-statistics";
import { api } from '@/lib/api';
import { TeamMemberStatisticsProps } from '@/components/dashboard/TeamDashboard/TeamMemberStatistics/types';


const getInitials = (name: string): string => !name ? "U" : name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
const formatMinutesToHours = (minutes: number): string => `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
const generatePlatformColor = (platform: string): string => {
     // Use platform name as seed for consistent colors
     let hash = 0;
     for (let i = 0; i < platform.length; i++) {
       const char = platform.charCodeAt(i);
       hash = ((hash << 5) - hash) + char;
       hash = hash & hash; // Convert to 32bit integer
     }

     // Generate HSL color with fixed saturation and lightness for consistency
     const hue = Math.abs(hash) % 360;
     return `hsl(${hue}, 65%, 55%)`;
    };

const UserActivityCard = React.memo(({ user, rank, totalMembers }: { user: CurrentUserStatistics, rank: number, totalMembers: number }) => {
  const isFirstPlace = rank === 1;
  const cardClasses = `flex items-center p-3 rounded-lg shadow-sm ${isFirstPlace ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200' : 'bg-white border border-gray'}`;

  UserActivityCard.displayName = 'UserActivityCard';
  return (
    <div className={cardClasses}>
      <div className="flex items-center gap-3 w-2/5">
        <div className="w-16 text-center">
            {isFirstPlace ? ( <Award className="w-6 h-6 text-yellow-500" /> ) : (
                <div className="flex items-baseline justify-center gap-1">
                    <span className="font-bold text-purple-600 text-xl">{rank}</span>
                    <span className="font-semibold text-gray-400 text-sm">/ {totalMembers}</span>
                </div>
            )}
        </div>
        <div className="w-9 h-9 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-full flex items-center justify-center font-bold text-white text-sm flex-shrink-0">{getInitials(user.full_name)}</div>
        <span className="font-semibold text-gray-800 truncate">{user.full_name}</span>
      </div>
      <div className="flex-1 text-center text-sm text-gray-600 flex items-center justify-center gap-1.5"><Clock className="w-4 h-4" />{formatMinutesToHours(user.user_team_learning_time_minutes)}</div>
          <div className="w-1/3 flex justify-end items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-green-600" title="Completed Paths"><Check className="w-4 h-4" /><span className="font-medium">{user.learning_path_progress_summary.completed.count}</span></div>
            <div className="flex items-center gap-1.5 text-yellow-600" title="Paths In Progress"><Hourglass className="w-4 h-4" /><span className="font-medium">{user.learning_path_progress_summary.in_progress.count}</span></div>
          </div>
    </div>
  );
});

const VerticalBar = ({ label, value, maxValue, icon: Icon, colorClass, delay }: { label: string, value: number, maxValue: number, icon: React.ElementType, colorClass: string, delay: number }) => {
  const percentageHeight = maxValue > 0 ? (value / maxValue) * 100 : 0;
  return (
    <motion.div className="flex flex-col items-center gap-2" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay }}>
      <p className="font-mono font-semibold text-purple-900 h-6">{formatMinutesToHours(value)}</p>
      <div className="w-16 h-48 bg-slate-200/70 rounded-t-lg flex items-end">
        <motion.div className={`w-full rounded-t-lg ${colorClass}`} initial={{ height: 0 }} animate={{ height: `${percentageHeight}%` }} transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: delay + 0.2 }} />
      </div>
      <p className="font-semibold text-sm text-slate-600 flex items-center gap-1.5"><Icon className="w-4 h-4 text-slate-400" />{label}</p>
    </motion.div>
  );
};

const ComparisonBar = React.memo(({ label, value, maxValue, colorClass, valueDisplay }: { label: string; value: number; maxValue: number; colorClass: string; valueDisplay: string; }) => {
    const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
    ComparisonBar.displayName = 'ComparisonBar';
    return (
        <div>
            <div className="flex justify-between items-center text-sm mb-1.5">
                <span className="font-semibold text-gray-700">{label}</span>
                <span className="font-mono text-xs font-medium text-gray-500">{valueDisplay}</span>
            </div>
            <div className="w-full bg-gray-200/70 rounded-full h-2.5 shadow-inner">
                <motion.div
                    className={`h-2.5 rounded-full ${colorClass || 'bg-gray-400'}`}
                    style={{ width: `${percentage}%` }}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
                />
            </div>
        </div>
    );
});

export default function TeamMemberStatistics({ teamId }: TeamMemberStatisticsProps) {

  const [stats, setStats] = useState<PersonalTeamStatisticsApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPersonalStatistics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getTeamStatisticsView(teamId) as PersonalTeamStatisticsApiResponse;
        setStats(data);
      } catch (err) {
        setError('Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    if (teamId) {
      loadPersonalStatistics();
    }
  }, [teamId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        <span className="ml-3 text-gray-600">Loading your statistics...</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️</div>
          <p className="text-gray-600">{error || 'No statistics available'}</p>
        </div>
      </div>
    );
  }

  // Extract data from API response
  const { user_stats, team_comparison_stats } = stats;
  const currentUser = user_stats;
  const rank = team_comparison_stats.rank;
  const averageMinutes = team_comparison_stats.average_learning_time_minutes;
  const totalMembers = team_comparison_stats.total_members;

  // Calculate comparison values
  const maxComparisonTime = Math.max(currentUser.user_team_learning_time_minutes, averageMinutes) * 1.2;
  const platformValues = Object.values(currentUser.platform_split_minutes);
  const maxPlatformTime = platformValues.length > 0 ? Math.max(...platformValues) : 0;

  if (!currentUser) {
    return <div className="p-8 text-center text-slate-500">User statistics not found.</div>;
  }

  const containerVariants: Variants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.15 } } };
  const itemVariants: Variants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } } };

  return (
    <motion.div className="space-y-6" variants={containerVariants} initial="hidden" animate="visible">
      <motion.div variants={itemVariants}>
        <h3 className="text-xl font-bold text-slate-800 mb-3 flex items-center gap-2"><User className="w-6 h-6 text-purple-600" />Your Position in Team</h3>
        <UserActivityCard user={currentUser} rank={rank} totalMembers={totalMembers} />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div className="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-lg transition-shadow" variants={itemVariants}>
          <h3 className="text-xl font-bold text-gray-800 mb-5 flex items-center gap-2.5"><BarChart className="w-6 h-6 text-purple-600" />Learning Time Comparison</h3>
          <div className="flex justify-center items-end gap-10 pt-4">
            <VerticalBar
              label="Your Time"
              value={currentUser.user_team_learning_time_minutes}
              maxValue={maxComparisonTime}
              icon={User}
              colorClass="bg-gradient-to-t from-purple-500 to-indigo-500"
              delay={0.1}
            />
            <VerticalBar
              label="Team Average"
              value={averageMinutes}
              maxValue={maxComparisonTime}
              icon={Users}
              colorClass="bg-gradient-to-t from-slate-400 to-slate-500"
              delay={0.2}
            />
          </div>
        </motion.div>

        <motion.div className="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-lg transition-shadow" variants={itemVariants}>
          <h3 className="text-xl font-bold text-gray-800 mb-5 flex items-center gap-2.5"><BrainCircuit className="w-6 h-6 text-purple-600" />Time by Platform</h3>
          <div className="space-y-4">
            {Object.entries(currentUser.platform_split_minutes)
              .sort(([, a], [, b]) => b - a)
              .map(([platform, minutes]) => (
                <ComparisonBar
                    key={platform}
                    label={platform}
                    value={minutes}
                    maxValue={maxPlatformTime}
                    colorClass={generatePlatformColor(platform)}
                    valueDisplay={formatMinutesToHours(minutes)}
                />
              ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}