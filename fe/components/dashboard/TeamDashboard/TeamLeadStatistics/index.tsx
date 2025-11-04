import React, {useEffect, useState} from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import { Award, BarChartHorizontalBig, BrainCircuit, Check, Clock, Hourglass, ChevronLeft, ChevronRight, X, BookCheck, ListTodo, CircleSlash, FileText } from 'lucide-react';
import { TeamDashboardApiResponse } from "@/types/team-statistics";
import { TeamLeadStatisticsProps } from '@/components/dashboard/TeamDashboard/TeamLeadStatistics/types';

const getInitials = (name: string): string => !name ? "U" : name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);

const MemberProgressModal = ({ member, onClose }: { member: any; onClose: () => void; }) => {
  const summary = member.learning_path_progress_summary;
  const listContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.07,
      },
    },
  };

  const listItemVariants = {
    hidden: { y: 15, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
    },
  };

  const PathListColumn = ({ title, icon, paths, colorClass, emptyIcon }: { title: string; icon: React.ReactNode; paths: any[], colorClass: string, emptyIcon: React.ReactNode }) => (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col h-full">
      <h4 className={`text-md font-bold mb-3 flex items-center gap-2.5 ${colorClass}`}>
        {icon}
        {title} <span className="text-sm font-medium bg-gray-200 text-gray-600 rounded-full px-2 py-0.5">{paths.length}</span>
      </h4>
      <div className="space-y-2 overflow-y-auto flex-grow max-h-[40vh] pr-1">
        {paths.length > 0 ? (
          <motion.ul variants={listContainerVariants} initial="hidden" animate="visible" className="space-y-2">
            {paths.map(path => (
              <motion.li key={path.id} variants={listItemVariants}>
                <div className="text-sm text-gray-800 bg-gray-50 p-2.5 rounded-md border border-gray-200/80 flex items-center gap-3">
                  <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <span className="font-medium">{path.title}</span>
                </div>
              </motion.li>
            ))}
          </motion.ul>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 py-4">
            {emptyIcon}
            <p className="text-sm mt-2 font-medium">No learning paths</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 20 }} onClick={(e) => e.stopPropagation()} className="bg-gray-100 rounded-2xl max-w-5xl w-full shadow-2xl relative">
          <div className="p-6 border-b border-gray-200">
            <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition-colors"><X className="w-6 h-6" /></button>
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-full flex items-center justify-center font-bold text-white text-2xl flex-shrink-0">
                {getInitials(member.full_name)}
              </div>
              <div>
                <p className="text-xs text-purple-700 font-semibold tracking-wider">MEMBER PROGRESS</p>
                <h3 className="text-2xl font-bold text-gray-900">{member.full_name}</h3>
              </div>
            </div>
          </div>

          <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <PathListColumn title="Completed" icon={<BookCheck size={20}/>} paths={summary.completed.paths} colorClass="text-green-600" emptyIcon={<BookCheck className="w-10 h-10"/>} />
            <PathListColumn title="In Progress" icon={<ListTodo size={20}/>} paths={summary.in_progress.paths} colorClass="text-yellow-600" emptyIcon={<ListTodo className="w-10 h-10"/>} />
            <PathListColumn title="Not Started" icon={<CircleSlash size={20}/>} paths={summary.unstarted.paths} colorClass="text-gray-500" emptyIcon={<CircleSlash className="w-10 h-10"/>} />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};


export default function TeamStatisticsDetails({ teamId }: TeamLeadStatisticsProps) {
  const [stats, setStats] = useState<TeamDashboardApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<any | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const ITEMS_PER_PAGE = 5;

  useEffect(() => {
    const loadTeamStatistics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getTeamStatisticsView(teamId) as TeamDashboardApiResponse;
        setStats(data);
      } catch (err) {
        setError('Failed to load team statistics');
      } finally {
        setLoading(false);
      }
    };

    if (teamId) {
      loadTeamStatistics();
    }
  }, [teamId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        <span className="ml-3 text-gray-600">Loading team statistics...</span>
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

  const { overall_progress: overallProgress, member_list: memberList, platform_summary: platformSummary } = stats;
  const totalPlatformMinutes = Object.values(platformSummary).reduce((sum, val) => sum + val, 0);

  const handleMemberClick = (member: any) => {
    setSelectedMember(member);
    setIsModalOpen(true);
  };

  const totalPages = Math.ceil(memberList.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedMembers = memberList.slice(startIndex, startIndex + ITEMS_PER_PAGE);

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

  const DonutChart = ({ percentage, size = 120, strokeWidth = 10, color }: { percentage: number, size?: number, strokeWidth?: number, color: string }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    return (
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} strokeWidth={strokeWidth} stroke="#e5e7eb" fill="transparent" />
          <motion.circle cx={size / 2} cy={size / 2} r={radius} strokeWidth={strokeWidth} stroke={color} fill="transparent" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: offset }} transition={{ duration: 1.2, ease: "easeOut" }} />
        </svg>
        <div className="absolute flex flex-col items-center justify-center"><span className="text-3xl font-bold text-gray-800">{`${Math.round(percentage)}%`}</span></div>
      </div>
    );
  };

  return (
    <>
      <motion.div className="space-y-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <div className="lg:col-span-2 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm hover:shadow-lg transition-shadow flex flex-col">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2"><BarChartHorizontalBig className="w-5 h-5 text-purple-600" /> Member Activity</h3>
            <div className="space-y-2 flex-grow">
              {paginatedMembers.map((member, index) => {
                const overallRank = startIndex + index;
                return (
                  <div key={member.user_id} onClick={() => handleMemberClick(member)} className={`flex items-center p-3 rounded-lg transition-all duration-300 cursor-pointer ${ overallRank === 0 ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 shadow-sm' : 'bg-gray-50 hover:bg-gray-100'}`}>
                    <div className="flex items-center gap-3 w-2/5">
                      <div className="w-6 text-center">{overallRank === 0 ? <Award className="w-6 h-6 text-yellow-500" /> : <span className="font-bold text-purple-600">{overallRank + 1}</span>}</div>
                      <div className="w-9 h-9 bg-gradient-to-br from-[#5E35B1] to-[#380A63] rounded-full flex items-center justify-center font-bold text-white text-sm flex-shrink-0">{getInitials(member.full_name)}</div>
                      <span className="font-semibold text-gray-800 truncate">{member.full_name}</span>
                    </div>
                    <div className="flex-1 text-center text-sm text-gray-600 flex items-center justify-center gap-1.5"><Clock className="w-4 h-4" /> {Math.round(member.team_learning_time_minutes / 60)}h {member.team_learning_time_minutes % 60}m</div>
                    <div className="w-1/3 flex justify-end items-center gap-4 text-xs">
                      <div className="flex items-center gap-1.5 text-green-600" title="Completed Paths"><Check className="w-4 h-4" /> <span className="font-medium">{member.learning_path_progress_summary.completed.count}</span></div>
                      <div className="flex items-center gap-1.5 text-yellow-600" title="Paths In Progress"><Hourglass className="w-4 h-4" /> <span className="font-medium">{member.learning_path_progress_summary.in_progress.count}</span></div>
                    </div>
                  </div>
                )
              })}
            </div>
            {totalPages > 1 && (<div className="flex justify-between items-center pt-4 mt-4 border-t border-gray-200"><button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronLeft className="w-4 h-4" />Previous</button><span className="text-sm text-gray-600">Page {currentPage} of {totalPages}</span><button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">Next<ChevronRight className="w-4 h-4" /></button></div>)}
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 flex flex-col items-center shadow-sm hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Overall Progress</h3>
            <DonutChart percentage={overallProgress.overall_completion_percentage} color="#8B5CF6" />
            <div className="w-full grid grid-cols-3 gap-3 text-center mt-4">
              <div className="bg-gray-50 border border-gray-200 p-3 rounded-lg"><p className="text-2xl font-bold text-green-600">{overallProgress.completed_user_lp_assignments}</p><p className="text-xs text-gray-500">Completed</p></div>
              <div className="bg-gray-50 border border-gray-200 p-3 rounded-lg"><p className="text-2xl font-bold text-yellow-500">{overallProgress.in_progress_user_lp_assignments}</p><p className="text-xs text-gray-500">In Progress</p></div>
              <div className="bg-gray-50 border border-gray-200 p-3 rounded-lg"><p className="text-2xl font-bold text-gray-500">{overallProgress.unstarted_user_lp_assignments}</p><p className="text-xs text-gray-500">Not Started</p></div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2"><BrainCircuit className="w-5 h-5 text-purple-600" /> Learning by Platform</h3>
            <div className="space-y-4 pt-2">
              {Object.entries(platformSummary).map(([platform, minutes]) => {
                const percentage = totalPlatformMinutes > 0 ? (minutes / totalPlatformMinutes) * 100 : 0;
                return (<div key={platform}><div className="flex justify-between items-center text-sm mb-1"><span className="font-semibold text-gray-700">{platform}</span><span className="font-mono text-gray-500">{Math.round(percentage)}%</span></div><div className="w-full bg-gray-200 rounded-full h-2"><div className="h-2 rounded-full" style={{ width: `${percentage}%`, backgroundColor: generatePlatformColor(platform) || '#333' }}></div></div></div>)
              })}
            </div>
          </div>
        </div>
      </motion.div>

      {isModalOpen && selectedMember && (
        <MemberProgressModal member={selectedMember} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
}