"use client"

import { useState, useEffect, type FC } from "react"
import { useRouter } from "next/router"
import { motion, AnimatePresence, type Variants } from "framer-motion"
import { useAuth } from "@/context/AuthContext"
import { api } from "@/lib/api"
import type { LearningPath } from "@/types/learning-paths"
import type { UserStatistics, Team } from "@/types/user-statistics"
import Certificate from "@/components/certificate/Certificate"
import StatisticsCharts from "@/pages/profile/StatisticsCharts"
import { Award, Target, CheckCircle, Trophy, Users, ArrowLeft, AlertCircle, Sparkles, Loader, Calendar, ArrowRight, BarChart3, Flame, Hash, } from "lucide-react"
import EnhancedBackground from "@/components/background/EnhancedBackground";


const formatFullName = (username: string, fullName?: string): string => {
    if (fullName) return fullName;
    if (!username) return "";
    return username
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
}

const StatCard: FC<{
  icon: FC<any>
  label: string
  value: number | string
  gradient: string
  delay?: number
}> = ({ icon: Icon, label, value, gradient, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 30, scale: 0.9 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    transition={{ type: "spring", stiffness: 300, damping: 20, delay: delay * 0.1 }}
    whileHover={{ scale: 1.03, y: -4, transition: { type: "spring", stiffness: 400, damping: 17 } }}
    className="relative bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-gray-100/50 group hover:shadow-lg hover:bg-white/90 transition-all duration-300 overflow-hidden"
  >
    <motion.div className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-500" style={{ background: gradient }} />
    <div className="relative flex items-center space-x-4">
      <div className="relative p-3 rounded-xl shadow-md" style={{ background: gradient }}>
        <Icon className="w-6 h-6 text-white" />
        <motion.div className="absolute inset-0 rounded-xl border-2 border-white/30" animate={{ scale: [1, 1.1, 1], opacity: [0.5, 0, 0.5] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }} />
      </div>
      <div className="flex-1">
        <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: delay * 0.1 + 0.2, type: "spring", stiffness: 300 }} className="text-2xl font-bold text-neutral-dark mb-1">
          <motion.span key={String(value)} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}>
            {value}
          </motion.span>
        </motion.div>
        <div className="text-sm text-neutral-secondary-light font-medium tracking-wide">{label}</div>
      </div>
    </div>
  </motion.div>
);

const LoadingSpinner: FC = () => (
  <div className="flex justify-center items-center p-8">
    <motion.div className="relative">
      <div className="absolute inset-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
        <Loader className="w-6 h-6 text-white" />
      </div>
    </motion.div>
  </div>
);

const ErrorDisplay: FC<{ message: string }> = ({ message }) => (
  <motion.div initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} className="flex justify-center items-center gap-3 p-6 text-red-600 bg-gradient-to-r from-red-50/80 to-pink-50/80 backdrop-blur-sm rounded-xl border border-red-200/50 shadow-sm">
    <motion.div animate={{ rotate: [0, 10, -10, 0] }} transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 2 }}>
      <AlertCircle className="w-5 h-5" />
    </motion.div>
    <p className="font-medium">{message}</p>
  </motion.div>
);

const NoDataMessage: FC<{ message: string }> = ({ message }) => (
  <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="text-center p-10 bg-gradient-to-br from-white/80 to-gray-50/80 backdrop-blur-sm rounded-xl border border-gray-100/50 shadow-sm">
    <motion.div animate={{ rotate: [0, 5, -5, 0], scale: [1, 1.05, 1] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} className="w-14 h-14 mx-auto mb-4 rounded-full bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
      <Sparkles className="w-7 h-7 text-white" />
    </motion.div>
    <p className="font-semibold text-neutral-dark">{message}</p>
  </motion.div>
);

const StreakDisplay: FC<{ streakDays: number; userCreatedAt?: string | null }> = ({ streakDays }) => {
  const hasStreak = streakDays > 0;

  const getStreakMessage = () => {
    if (streakDays === 0) return "Start your learning streak today!";
    return `${streakDays} day streak! Keep it going!`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="mt-4 text-center"
    >
      <div className="inline-flex items-center justify-center gap-2">
        <motion.div
          animate={{ scale: hasStreak ? [1, 1.15, 1] : 1 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut', repeatType: 'mirror' }}
        >
          <Flame className={`h-8 w-8 transition-colors duration-300 ${hasStreak ? 'text-red-500' : 'text-slate-400'}`} />
        </motion.div>
        <p className="text-4xl font-bold tracking-tight text-neutral-dark">
          {streakDays}
        </p>
      </div>
      <p className="mt-2 px-4 text-sm text-neutral-secondary-light">{getStreakMessage()}</p>
    </motion.div>
  );
};

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [userStats, setUserStats] = useState<UserStatistics | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errors, setErrors] = useState<{
    stats: string | null;
    teams: string | null;
    paths: string | null;
  }>({ stats: null, teams: null, paths: null });
  const [activeTab, setActiveTab] = useState<"statistics" | "teams" | "certificates">("statistics");
  const [showCertModal, setShowCertModal] = useState(false);
  const [currentPath, setCurrentPath] = useState<LearningPath | null>(null);
  const [totalModulesForCert, setTotalModulesForCert] = useState(0);
  const [, setIsCertLoading] = useState(false);
  const [timePeriod] = useState(7);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
        router.replace('/login');
        return;
    }
    if (user?.id) {
        setIsLoading(true);
        setErrors({ stats: null, teams: null, paths: null });

        Promise.allSettled([
            api.getUserStatistics(user.id), // Single endpoint call
            api.getMyTeams(),
            api.getUserLearningPaths(user.id),
        ]).then(([statRes, teamRes, pathRes]) => {
            if (statRes.status === "fulfilled") {
              const stats = statRes.value as UserStatistics;
              setUserStats(stats);
            } else {
              setErrors(p => ({ ...p, stats: "Failed to load stats." }));
            }

            if (teamRes.status === "fulfilled") setTeams(teamRes.value);
            else setErrors(p => ({ ...p, teams: "Failed to load teams." }));

            if (pathRes.status === "fulfilled") setPaths(pathRes.value);
            else setErrors(p => ({ ...p, paths: "Failed to load learning paths." }));
        }).finally(() => setIsLoading(false));
    }
  }, [user?.id, authLoading, isAuthenticated, router]);

  const handleShowCertificate = async (path: LearningPath) => {
    setCurrentPath(path);
    setShowCertModal(true);
    setIsCertLoading(true);
    setTotalModulesForCert(0);
    try {
      const response = await api.getLearningPath(path.id);
      setTotalModulesForCert(response.modules.length);
    } catch (error) {}
    finally {
      setIsCertLoading(false);
    }
  };

  const handleTeamClick = (teamId: string) => {
    router.push(`/teams/${teamId}`);
  };

  if (authLoading || (!user && !authLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center relative">
        <EnhancedBackground />
        <LoadingSpinner />
      </div>
    );
  }

  const completedPaths = paths.filter(p => p.completion_percentage === 100);
  const displayName = formatFullName(user?.username || '', user?.full_name);
  const initials = displayName.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);

  const containerVariants: Variants = { 
    hidden: { opacity: 0 }, 
    visible: { opacity: 1, transition: { staggerChildren: 0.12, delayChildren: 0.15, duration: 0.6 } } 
  };
  const itemVariants: Variants = { 
    hidden: { opacity: 0, y: 25, scale: 0.95 }, 
    visible: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 300, damping: 25 } } 
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <EnhancedBackground />
      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-8 relative">
        <motion.button
  onClick={() => router.back()}
  initial={{ opacity: 0, y: -4 }}
  animate={{ opacity: 1, y: 0 }}
  whileHover="hover"
  whileTap={{ scale: 0.98 }}
  variants={{}}
  transition={{ type: "spring", stiffness: 300, damping: 22 }}
  className="absolute top-10 left-10 z-20 inline-flex items-center gap-2 text-purple-700 hover:text-purple-800 font-bold text-lg tracking-tight antialiased select-none transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-400/70 focus-visible:rounded-md"
  aria-label="Go back"
>
  <motion.span
    className="inline-flex origin-left"
    variants={{ hover: { x: -2, scale: 1.12 } }}
    transition={{ type: "spring", stiffness: 300, damping: 18 }}
  >
    <ArrowLeft className="w-5 h-5" strokeWidth={2.5} />
  </motion.span>

  <motion.span
    className="origin-left"
    variants={{ hover: { scale: 1.06 } }}
    transition={{ type: "spring", stiffness: 300, damping: 18 }}
  >
    Back
  </motion.span>
</motion.button>



        
        <motion.div variants={containerVariants} initial="hidden" animate="visible" className="lg:col-span-1 space-y-6">
          <motion.div variants={itemVariants} className="relative bg-white/70 backdrop-blur-xl rounded-xl p-6 shadow-lg border border-gray-100/30 text-center group hover:shadow-xl hover:bg-white/80 transition-all duration-500 overflow-hidden">
            <motion.div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 via-purple-50/30 to-pink-50/30 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10">
              <motion.div whileHover={{ scale: 1.08, rotate: 3 }} transition={{ type: "spring", stiffness: 300, damping: 20 }} className="relative w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 bg-gradient-to-r from-primary to-accent shadow-lg">
                {initials}
                <motion.div className="absolute inset-0 rounded-full border-3 border-white/30" animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }} />
              </motion.div>
              <motion.h2 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }} className="text-2xl font-bold text-neutral-dark mb-2">
                {displayName}
              </motion.h2>
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }} className="flex items-center justify-center gap-2 text-sm text-neutral-secondary-light mb-3">
                {userStats?.user_created_at && (
                  <>
                    <Calendar className="w-4 h-4" />
                    <span>Member since {new Date(userStats.user_created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
                  </>
                )}
              </motion.div>
              <StreakDisplay 
                streakDays={userStats?.streak_days || 0} 
              />
            </div>
          </motion.div>
          
          <motion.div variants={itemVariants} className="space-y-5">
            {isLoading ? <LoadingSpinner /> : errors.stats ? <ErrorDisplay message={errors.stats} /> : (
              <>
                <StatCard icon={Target} label="Completed Courses" value={userStats?.completed_learning_paths || 0} gradient="linear-gradient(135deg, #8B5CF6, #7C3AED)" delay={0} />
                <StatCard icon={CheckCircle} label="Modules Finished" value={userStats?.modules_completed || 0} gradient="linear-gradient(135deg, #10B981, #059669)" delay={1} />
                <StatCard icon={Trophy} label="Skill Points" value={userStats?.skill_points_earned || 0} gradient="linear-gradient(135deg, #F59E0B, #D97706)" delay={2} />
                <StatCard icon={Award} label="Quizzes Passed" value={userStats?.quizzes_completed || 0} gradient="linear-gradient(135deg, #3B82F6, #1D4ED8)" delay={3} />
              </>
            )}
          </motion.div>
        </motion.div>
        
        <div className="lg:col-span-2">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mb-6 bg-white/70 backdrop-blur-xl rounded-xl p-2 shadow-lg border border-gray-100/30 flex gap-1">
            {['statistics', 'teams', 'certificates'].map(tab => (
              <motion.button key={tab} onClick={() => setActiveTab(tab as any)} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className={`flex-1 flex items-center justify-center gap-2 text-sm font-semibold px-3 py-3 rounded-lg transition-all duration-300 relative overflow-hidden ${activeTab === tab ? "text-white shadow-md" : "text-neutral-secondary-light hover:text-neutral-dark hover:bg-gray-50/50"}`}>
                {activeTab === tab && <motion.div layoutId="activeTab" className="absolute inset-0 bg-gradient-to-r from-primary/80 to-primary" transition={{ type: "spring", stiffness: 300, damping: 30 }} />}
                {tab === 'statistics' && <BarChart3 className="w-4 h-4 relative z-10" />}
                {tab === 'teams' && <Users className="w-4 h-4 relative z-10" />}
                {tab === 'certificates' && <Award className="w-4 h-4 relative z-10" />}
                <span className="relative z-10 capitalize">{tab}</span>
              </motion.button>
            ))}
          </motion.div>

          <AnimatePresence mode="wait">
            {activeTab === "certificates" && (
              <motion.div key="certs" variants={itemVariants} initial="hidden" animate="visible" exit={{ opacity: 0, scale: 0.95, y: 20 }} className="space-y-6">
                <motion.h3 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-xl font-bold text-neutral-dark">My Certificates</motion.h3>
                {isLoading ? <LoadingSpinner /> : errors.paths ? <ErrorDisplay message={errors.paths} /> : completedPaths.length === 0 ? <NoDataMessage message="You haven't completed any learning paths yet. Keep learning!" /> : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {completedPaths.map((path, index) => (
                      <motion.div key={path.id} initial={{ opacity: 0, y: 30, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: index * 0.1, type: "spring", stiffness: 300, damping: 25 }} whileHover={{ scale: 1.03, y: -6, transition: { type: "spring", stiffness: 400, damping: 17 } }} className="relative bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-100/30 cursor-pointer group shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-500 overflow-hidden" onClick={() => handleShowCertificate(path)}>
                        <motion.div className="absolute inset-0 bg-gradient-to-br from-blue-50/40 via-purple-50/40 to-pink-50/40 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <div className="relative z-10 flex items-start gap-4 mb-4">
                          <div className="flex-1">
                            <p className="text-lg font-bold text-neutral-dark group-hover:text-purple-600 transition-colors duration-300 mb-2">{path.title}</p>
                            <div className="flex items-center gap-2 text-sm text-neutral-secondary-light"><Calendar className="w-4 h-4" /><span>Completed</span></div>
                          </div>
                          <div className="flex-shrink-0 p-2 rounded-xl bg-gradient-to-r from-purple-400/20 to-blue-400/20 group-hover:from-purple-400/30 group-hover:to-blue-400/30 transition-all duration-300"><Award className="w-6 h-6 text-purple-600" /></div>
                        </div>
                        <motion.div className="relative z-10 flex items-center gap-2 text-purple-600 font-semibold text-sm group-hover:text-purple-700 transition-colors duration-300" whileHover={{ x: 3 }}>
                          <span>View Certificate</span><ArrowRight className="w-4 h-4" />
                        </motion.div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
            {activeTab === "teams" && (
              <motion.div key="teams" variants={itemVariants} initial="hidden" animate="visible" exit={{ opacity: 0, scale: 0.95, y: 20 }} className="space-y-6">
                <motion.h3 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-xl font-bold text-neutral-dark">My Teams</motion.h3>
                {isLoading ? <LoadingSpinner /> : errors.teams ? <ErrorDisplay message={errors.teams} /> : teams.length === 0 ? <NoDataMessage message="You are not a member of any team yet. Join one to collaborate!" /> : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {teams.map((team, index) => (
                      <motion.div key={team.id} initial={{ opacity: 0, y: 30, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: index * 0.1, type: "spring", stiffness: 300, damping: 25 }} whileHover={{ scale: 1.03, y: -4, transition: { type: "spring", stiffness: 400, damping: 17 } }} className="relative bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-100/30 group shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-500 overflow-hidden cursor-pointer" onClick={() => handleTeamClick(team.id)}>
                        <motion.div className="absolute inset-0 bg-gradient-to-br from-green-50/40 via-blue-50/40 to-purple-50/40 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <div className="relative z-10 flex items-start space-x-4">
                            <motion.div whileHover={{ scale: 1.1, rotate: 5 }} transition={{ type: "spring", stiffness: 300, damping: 20 }} className="flex-shrink-0 p-3 rounded-xl bg-gradient-to-r from-primary/20 to-accent/20 group-hover:from-primary/30 group-hover:to-accent/30 transition-all duration-300">
                                <Users className="w-6 h-6 text-primary" />
                            </motion.div>
                            <div className="flex-1">
                                <p className="text-lg font-bold text-neutral-dark uppercase tracking-wide mb-1 group-hover:text-primary transition-colors duration-300">{team.name}</p>
                                <div className="flex items-center gap-1 text-sm text-neutral-secondary-light mb-3">
                                    <Hash className="w-4 h-4" />
                                    <span>{team.members?.length || 0} member{team.members?.length !== 1 ? "s" : ""}</span>
                                </div>
                            </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
            {activeTab === "statistics" && (
              <motion.div key="statistics" variants={itemVariants} initial="hidden" animate="visible" exit={{ opacity: 0, scale: 0.95, y: 20 }} className="space-y-6">
                <motion.h3 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-xl font-bold text-neutral-dark">Learning Analytics</motion.h3>
                {errors.stats ? (
                  <ErrorDisplay message={errors.stats} />
                ) : !userStats ? (
                  <LoadingSpinner />
                ) : (
                  <StatisticsCharts
                    statistics={userStats}
                    timePeriod={timePeriod}
                    userId={user!.id}
                  />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
      
      {/* Certificate Modal */}
      {currentPath && (
        <Certificate
          isOpen={showCertModal}
          onClose={() => setShowCertModal(false)}
          userName={formatFullName(user?.username || '', user?.full_name)}
          pathTitle={currentPath.title}
          completionDate={new Date()}
          totalModules={totalModulesForCert}
          estimatedDays={currentPath.estimated_days}
        />
      )}
    </div>
  )
}
