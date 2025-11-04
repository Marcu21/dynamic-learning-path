import {useState, useEffect, useCallback, useRef} from 'react';
import {useRouter} from 'next/router';
import {motion, AnimatePresence} from 'framer-motion';
import {useAuth} from '@/context/AuthContext';
import {useNotifications} from '@/context/NotificationContext';
import {api} from '@/lib/api';
import LearningPathDisplay from '@/components/learning-path/LearningPathDisplay';
import ProgressTracker from '@/components/learning-path/ProgressTracker';
import Button from '@/components/common/Button';
import Certificate from '@/components/certificate/Certificate';
import PathSelector from '@/components/learning-path/PathSelector';
import {variantStyles} from '@/components/common/Button/styles'
import {LearningPath, Module, LearningPathFE, PreferencesCreate} from '@/types/learning-paths';
import {
    ArrowLeft,
    Clock,
    CheckCircle,
    HelpCircle,
    Star,
    BarChart3,
    Dna,
    Target,
    BookOpen,
    Tv,
    Code
} from 'lucide-react';
import BackgroundBlobs from '@/components/background/BackgroundBlobs';
import GenerationDetailsCard from "@/components/learning-path/GenerationDetailsCard";
import React from 'react';

const GenerationDetails = ({preferences}: { preferences: PreferencesCreate }) => {
    const formatLabel = (str: string) => str.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    const [isGoalExpanded, setIsGoalExpanded] = useState(false);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
    const [isGoalTruncated, setIsGoalTruncated] = useState(false);
    const goalRef = useRef<HTMLParagraphElement>(null);

    useEffect(() => {
      const el = goalRef.current;
      if (!el) return;

      const check = () => {
        setIsGoalTruncated(el.scrollWidth > el.clientWidth);
      };

      check();
      const ro = new ResizeObserver(check);
      ro.observe(el);
      return () => ro.disconnect();
    }, [preferences.subject]);


    const MAX_VISIBLE_TAGS = 2;

    const toggleSectionExpansion = (key: string) => {
        setExpandedSections(prev => ({...prev, [key]: !prev[key]}));
    };

    const tagColorSchemes = {
        experience: {
            bg: 'bg-orange-100',
            text: 'text-neutral-dark',
            border: 'border-orange-200'
        },
        study_time: {
            bg: 'bg-teal-100',
            text: 'text-neutral-dark',
            border: 'border-teal-200'
        },
        learning_style: {
            bg: 'bg-purple-100',
            text: 'text-neutral-dark',
            border: 'border-purple-200'
        },
        prefered_platforms: {
            bg: 'bg-sky-100',
            text: 'text-neutral-dark',
            border: 'border-sky-200'
        }
    };

    const renderTags = (key: string, tags: string[], colors: {
        bg: string,
        text: string,
        border: string
    }, shouldFormatLabel = false) => {
        const isExpanded = expandedSections[key];
        const visibleTags = isExpanded ? tags : tags.slice(0, MAX_VISIBLE_TAGS);
        const hiddenCount = tags.length - MAX_VISIBLE_TAGS;

        return (
            <div className="flex flex-wrap gap-2 justify-end items-center">
                {visibleTags.map(tag => (
                    <span key={tag}
                          className={`${colors.bg} ${colors.text} text-sm font-medium px-3 py-1 rounded-full border ${colors.border} shadow-sm`}>
            {shouldFormatLabel ? formatLabel(tag) : tag}
          </span>
                ))}
                {!isExpanded && hiddenCount > 0 && (
                    <button onClick={() => toggleSectionExpansion(key)}
                            className="bg-gray-200 text-gray-700 text-sm font-semibold px-3 py-1 rounded-full border border-gray-300 shadow-sm hover:bg-gray-300 transition-colors">
                        +{hiddenCount}
                    </button>
                )}
                {isExpanded && hiddenCount > 0 && (
                    <button onClick={() => toggleSectionExpansion(key)}
                            className="bg-gray-200 text-gray-700 text-sm font-semibold px-3 py-1 rounded-full border border-gray-300 shadow-sm hover:bg-gray-300 transition-colors">
                        See less
                    </button>
                )}
            </div>
        );
    };


    const detailItems = [
        {
            key: 'subject',
            label: 'Goal',
            icon: Target,
            color: 'text-primary',
            shouldRender: !!preferences.subject,
            render: () => {
                const showReadMoreButton = isGoalTruncated || (preferences.subject?.length ?? 0) > 100;

                  if (isGoalExpanded) {
                    return (
                      <div>
                        <p className="text-neutral-dark text-left">{preferences.subject}</p>
                        {showReadMoreButton && (
                          <button onClick={() => setIsGoalExpanded(false)}
                                  className="text-primary text-md font-semibold text-sm mt-1 hover:underline">
                            See less
                          </button>
                        )}
                      </div>
                    );
                  }

                  return (
                    <div className="flex items-baseline min-w-0 gap-2">
                      <p
                        ref={goalRef}
                        className="text-neutral-dark tracking-tight truncate flex-1 min-w-0"
                      >
                        {preferences.subject}
                      </p>
                      {showReadMoreButton && (
                        <button
                          onClick={() => setIsGoalExpanded(true)}
                          className="text-primary text-md font-bold hover:underline flex-shrink-0"
                        >
                          See more
                        </button>
                      )}
                    </div>
                  );
                }
        },
        {
            key: 'experience',
            label: 'Experience',
            icon: BookOpen,
            color: 'text-orange-500',
            shouldRender: !!preferences.experience_level,
            render: (key: string) => renderTags(
                key,
                [formatLabel(preferences.experience_level!)],
                tagColorSchemes.experience
            )
        },
        {
            key: 'study_time',
            label: 'Daily Time',
            icon: Clock,
            color: 'text-teal-500',
            shouldRender: !!preferences.study_time_minutes,
            render: (key: string) => renderTags(
                key,
                [`${preferences.study_time_minutes} min`],
                tagColorSchemes.study_time
            )
        },
        {
            key: 'learning_style',
            label: 'Styles',
            icon: Code,
            color: 'text-purple-500',
            shouldRender: preferences.learning_styles && preferences.learning_styles.length > 0,
            render: (key: string) => renderTags(
                key,
                preferences.learning_styles!,
                tagColorSchemes.learning_style,
                true
            )
        },
        {
            key: 'prefered_platforms',
            label: 'Platforms',
            icon: Tv,
            color: 'text-sky-500',
            shouldRender: preferences.preferred_platforms && preferences.preferred_platforms.length > 0,
            render: (key: string) => renderTags(
                key,
                preferences.preferred_platforms!,
                tagColorSchemes.prefered_platforms
            )
        }
    ];

    return (
        <div className="font-sans p-2">
            <div className="grid grid-cols-[auto,1fr] items-center gap-x-4 gap-y-4">
                {detailItems
                    .filter(item => item.shouldRender)
                    .map(({key, label, icon: Icon, color, render}) => (
                        <React.Fragment key={key}>
                            <div className="flex items-center font-bold text-neutral-dark self-center">
                                <Icon className={`w-5 h-5 mr-2.5 flex-shrink-0 ${color}`} strokeWidth={2.5}/>
                                <span>{label}</span>
                            </div>
                            <div className="flex justify-end text-right font-normal text-neutral-dark min-w-0">
                                {render(key)}
                            </div>
                        </React.Fragment>
                    ))}
            </div>
        </div>
    );
};

const LearningAnalytics = ({completedModulesCount, timeInvestedInPath, questionsAnswered, skillPoints}: {
    completedModulesCount: number,
    timeInvestedInPath: number,
    questionsAnswered: number,
    skillPoints: number
}) => {
    const analyticsItems = [
        {
            label: "Time Invested",
            value: `${timeInvestedInPath}m`,
            icon: Clock,
            color: "bg-primary-light text-purple-800"
        },
        {
            label: "Modules Completed",
            value: completedModulesCount,
            icon: CheckCircle,
            color: "bg-success-light text-green-800"
        },
        {
            label: "Correct Answers",
            value: questionsAnswered || 0,
            icon: HelpCircle,
            color: "bg-yellow-100 text-yellow-800"
        },
        {label: "Total Skill Points", value: skillPoints || 0, icon: Star, color: "bg-blue-100 text-blue-800"},
    ];

    return (
        <motion.div
            className="bg-white rounded-xl shadow-lg p-6"
        >
            <h3 className="flex items-center text-lg font-display font-semibold mb-4 text-neutral-dark">
                <BarChart3 className="w-5 h-5 mr-2 text-primary"/>
                Learning Analytics
            </h3>
            <div className="space-y-3">
                {analyticsItems.map(({label, value, icon: Icon, color}) => (
                    <div key={label}
                         className={`flex items-center justify-between p-3 rounded-lg ${color} hover:scale-105 transition-transform duration-200`}>
                        <div className="flex items-center font-sans font-medium ">
                            <Icon className="w-5 h-5 mr-3 text"/>
                            <span className="text-black">{label}</span>
                        </div>
                        <span className="font-bold text-lg">{value}</span>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

export default function PathPage() {
    const {user, isAuthenticated, isLoading} = useAuth();
    const {registerTaskCompletionHandler, generationCompletionEvent, clearGenerationEvent} = useNotifications();
    const router = useRouter();
    const {pathId, teamId} = router.query;

    const [currentPath, setCurrentPath] = useState<LearningPath | null>(null);
    const [modules, setModules] = useState<Module[]>([]);
    const [currentModule, setCurrentModule] = useState<Module | null>(null);
    const [completedModules, setCompletedModules] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [moduleCompletionLoading, setModuleCompletionLoading] = useState<Set<number>>(new Set());
    const [completionSuccessMessage, setCompletionSuccessMessage] = useState<string | null>(null);
    const [showCertificate, setShowCertificate] = useState(false);
    const [userStatistics, setUserStatistics] = useState<any>(null);
    const [availablePaths, setAvailablePaths] = useState<LearningPathFE[]>([]);
    const [isGeneratingModules, setIsGeneratingModules] = useState(false);
    const [generatingModules, setGeneratingModules] = useState<Set<number | string>>(new Set());
    const [preferences, setPreferences] = useState<PreferencesCreate | null>(null);
    const [timeSpentData, setTimeSpentData] = useState<number>(0);
    const [isTeamLead, setIsTeamLead] = useState(false);

    // Helper function to refresh progress data
    const refreshProgressData = useCallback(async () => {
        if (user?.id && currentPath?.id) {
            try {
                const progressData = await api.getLearningPathProgress(user.id, currentPath.id);
                const questionsAnswered = progressData?.questions_answered || 0;
                const skillPoints = progressData?.skill_points_earned || 0;
                const timeSpent = progressData?.total_time_spent_minutes || 0;
                setUserStatistics({questions_answered: questionsAnswered, skill_points: skillPoints});
                setTimeSpentData(timeSpent);
            } catch (error) {
            }
        }
    }, [user?.id, currentPath?.id]);


    const loadPath = useCallback(async (pathIdNum: number, teamIdStr?: string | string[]) => {
        if (!user?.id) return;
        setLoading(true);
        try {
            const allPathsPromise = teamIdStr
                ? api.getTeamLearningPaths(teamIdStr as string)
                : api.getUserLearningPaths(user.id);

            // Adăugat: Preluăm detaliile echipei dacă teamId este prezent
            const teamPromise = teamIdStr ? api.getTeam(teamIdStr as string) : Promise.resolve(null);

            const [pathDetails, progressData, preferencesResponse, allPathsResponse, teamDetails] = await Promise.all([
                api.getLearningPath(pathIdNum),
                api.getLearningPathProgress(user.id, pathIdNum),
                api.getLearningPathPreferences(pathIdNum).catch(() => {
                    return {success: false, data: null, message: 'Preferences not available'};
                }),
                allPathsPromise,
                teamPromise
            ]);

            // Adăugat: Setăm 'isTeamLead' pe baza detaliilor echipei
            if (teamDetails) {
                setIsTeamLead(teamDetails.team_lead_id === user.id);
            } else {
                setIsTeamLead(false);
            }

            const {learning_path, modules} = pathDetails;

            let completedModuleIds: Set<number> = new Set();
            if (progressData && Array.isArray(progressData.modules)) {
                completedModuleIds = new Set(
                    progressData.modules
                        .filter((mod: any) => mod.is_completed)
                        .map((mod: any) => mod.id)
                );
            }

            const questionsAnswered = progressData?.questions_answered || 0;
            const skillPoints = progressData?.skill_points_earned || 0;
            const timeSpent = progressData?.total_time_spent_minutes || 0;

            setCurrentPath(learning_path);
            setPreferences(preferencesResponse);
            setModules(modules);
            setCompletedModules(completedModuleIds);
            setUserStatistics({questions_answered: questionsAnswered, skill_points: skillPoints});
            setTimeSpentData(timeSpent);

            const pathsArray = Array.isArray(allPathsResponse)
                ? allPathsResponse
                : allPathsResponse.learning_paths || [];
            setAvailablePaths(pathsArray);

            const firstIncomplete = modules.find(m => !completedModuleIds.has(m.id));
            setCurrentModule(firstIncomplete || null);

        } catch (error: any) {
            if (error.status === 404) {
                router.push(teamIdStr ? `/teams/${teamIdStr}?error=path_not_found` : '/dashboard?error=path_not_found');
            } else {
                router.push(teamIdStr ? `/teams/${teamIdStr}` : '/dashboard');
            }
        } finally {
            setLoading(false);
        }
    }, [user?.id, router]);

    // Handle generation completion events for module updates
    useEffect(() => {
        if (generationCompletionEvent && currentPath?.id === generationCompletionEvent.learning_path?.id) {
            // Clear all generating states
            setGeneratingModules(new Set())
            setIsGeneratingModules(false);

            // Refresh the path data to get new modules
            if (pathId && typeof pathId === 'string' && user?.id) {
                loadPath(parseInt(pathId), teamId);
            }

            // Clear the event so it doesn't fire again
            clearGenerationEvent();
        }
    }, [generationCompletionEvent, currentPath?.id, clearGenerationEvent, pathId, teamId, user?.id, loadPath]);

    // Real-time module updates via WebSocket - handle both path generation and module insertion
    useEffect(() => {
        const handleTaskCompletion = (taskId: string, result: any) => {
            // Handle module insertion specifically
            if (taskId === 'module_inserted') {
                if (result?.learning_path_id && currentPath?.id === result.learning_path_id) {
                    // Refresh the path data to get new modules
                    if (pathId && typeof pathId === 'string' && user?.id) {
                        loadPath(parseInt(pathId), teamId).then(() => {
                            // Clear generating states
                            setGeneratingModules(new Set());
                            setIsGeneratingModules(false);

                            // Clean up sessionStorage
                            try {
                                if (currentPath?.id) {
                                    sessionStorage.removeItem(`generatingModules-${currentPath.id}`);
                                }
                            } catch (e) {
                            }
                        });
                    }
                }
                return;
            }

            // Handle other task completions (existing code)
            if (result?.learning_path_id && currentPath?.id === result.learning_path_id) {
                if (pathId && typeof pathId === 'string' && user?.id) {
                    loadPath(parseInt(pathId), teamId).then(() => {
                        if (result?.created_module_id) {
                            setGeneratingModules(new Set());
                            setIsGeneratingModules(false);

                            try {
                                if (currentPath?.id) {
                                    sessionStorage.removeItem(`generatingModules-${currentPath.id}`);
                                }
                            } catch (e) {
                            }
                        }
                    });
                }
            }
        };

        // Register the task completion handler
        registerTaskCompletionHandler(handleTaskCompletion);

        return () => {
        };
    }, [registerTaskCompletionHandler, currentPath?.id, pathId, teamId, user?.id, loadPath]);

    // Check if path is still being generated (has no modules but exists)
    useEffect(() => {
        if (currentPath && modules.length === 0 && !loading) {
            setIsGeneratingModules(true);
        } else if (modules.length > 0 && isGeneratingModules) {
            // Only turn off generating if it was on and we now have modules
            setIsGeneratingModules(false);
        }
    }, [currentPath, modules.length, loading, isGeneratingModules]);

    // Handle module insertion with platform support
    const handleInsertModule = async (afterIndex: number, query: string, platformName?: string) => {
        if (!currentPath?.id || !user?.id) return;

        // Create a unique identifier for this insertion operation
        const insertionId = `${currentPath.id}-${afterIndex}-${Date.now()}`

        // Add generating state for this insertion
        setGeneratingModules(prev => {
            const newSet = new Set(prev).add(insertionId);
            // Persist to sessionStorage for page refresh resilience
            try {
                sessionStorage.setItem(`generatingModules-${currentPath.id}`, JSON.stringify(Array.from(newSet)));
            } catch (e) {
            }
            return newSet;
        });

        try {
            await api.insertBridgeModule(
                currentPath.id,
                afterIndex + 2,
                user.id,
                query,
                true, // generateQuiz
                platformName || null
            );

        } catch (error) {
            // Remove generating state on error
            setGeneratingModules(prev => {
                const newSet = new Set(prev);
                newSet.delete(insertionId);
                // Update sessionStorage
                try {
                    if (currentPath?.id) {
                        sessionStorage.setItem(`generatingModules-${currentPath.id}`, JSON.stringify(Array.from(newSet)));
                    }
                } catch (e) {
                }
                return newSet;
            });
        }
    };

    useEffect(() => {
        if (pathId && typeof pathId === 'string' && user?.id && !isLoading) {
            // Restore generating modules state from sessionStorage
            try {
                const storedGeneratingModules = sessionStorage.getItem(`generatingModules-${pathId}`);
                if (storedGeneratingModules) {
                    const parsedModules = JSON.parse(storedGeneratingModules);
                    if (Array.isArray(parsedModules) && parsedModules.length > 0) {
                        setGeneratingModules(new Set(parsedModules));
                    }
                }
            } catch (e) {
            }

            loadPath(parseInt(pathId), teamId);
        }
    }, [pathId, teamId, user?.id, isLoading, loadPath]);

    const handleModuleAction = async (action: 'complete', module: Module) => {
        if (!user?.id) return;
        setModuleCompletionLoading(prev => new Set(prev).add(module.id));
        try {
            await api.markModuleComplete(module.id, user.id, module.duration);

            const newCompleted = new Set(completedModules).add(module.id);
            setCompletedModules(newCompleted);

            setCompletionSuccessMessage(`"${module.title}" marked as complete!`);
            setTimeout(() => setCompletionSuccessMessage(null), 3000);

            // Refresh progress data to get updated stats
            setTimeout(() => {
                refreshProgressData();
            }, 500);

        } catch (error) {
        } finally {
            setModuleCompletionLoading(prev => {
                const newSet = new Set(prev);
                newSet.delete(module.id);
                return newSet;
            });
        }
    };

    if (isLoading || loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!isAuthenticated || !currentPath) {
        return null;
    }

    const isPathComplete = modules.length > 0 && completedModules.size === modules.length;
    const timeInvestedInPath = timeSpentData;
    const isTeamContext = !!teamId;
    const backButtonUrl = isTeamContext ? `/teams/${teamId}` : '/dashboard';

    return (
        <motion.div
            className="bg-gray-50 relative overflow-hidden min-h-screen flex"
            initial="visible"
        >
            <BackgroundBlobs/>
            <AnimatePresence>
                {completionSuccessMessage && (
                    <motion.div
                        layout
                        initial={{y: -100, opacity: 0}}
                        animate={{y: 20, opacity: 1}}
                        exit={{y: -100, opacity: 0}}
                        transition={{type: "spring", stiffness: 300, damping: 25}}
                        className="fixed top-0 left-1/2 -translate-x-1/2 z-50"
                    >
                        <div
                            className="mt-4 flex items-center space-x-2 bg-green-100 text-black font-medium px-7 py-3 rounded-lg shadow-lg border-l-4 border-green-700">
                            <CheckCircle className="w-5 h-5 text-green-700"/> {}
                            <span>{completionSuccessMessage}</span>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {showCertificate && (
                    <Certificate
                        isOpen={showCertificate}
                        onClose={() => setShowCertificate(false)}
                        userName={user?.username || user?.email || ''}
                        pathTitle={currentPath.title}
                        completionDate={new Date()}
                        totalModules={modules.length}
                        estimatedDays={currentPath.estimated_days}
                    />
                )}
            </AnimatePresence>

            <div className="max-w-7xl mx-auto px-4 py-8 relative z-10 flex-grow">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                    <div className="lg:col-span-2 space-y-6">
                        <motion.div
                            className="bg-white rounded-xl shadow-lg p-4 flex flex-col sm:flex-row gap-4 items-center">
                            {/* MODIFICATION: Replaced simple text button with icon and text */}
                            <Button variant="hollow"
                                    onClick={() => router.push(backButtonUrl)}
                                    className="flex-shrink-0">
                 <span className="flex items-center gap-2 font-bold">
                    <ArrowLeft strokeWidth={2.5} className="w-4 h-4"/>
                     {isTeamContext ? "Back to Team Dashboard" : "Back to Dashboard"}
                 </span>
                            </Button>
                            <div className="flex-grow w-full pl-20 min-w-0">
                                <PathSelector
                                    paths={availablePaths}
                                    currentPathId={currentPath.id}
                                    onSelectPath={(path) => router.push(
                                        isTeamContext ? `/paths/${path.id}?teamId=${teamId}` : `/paths/${path.id}`
                                    )}
                                />
                            </div>
                        </motion.div>

                        <motion.div>
                            <LearningPathDisplay
                                title={currentPath.title}
                                path={currentPath}
                                modules={modules}
                                onModuleSelect={setCurrentModule}
                                onModuleComplete={(module) => handleModuleAction('complete', module)}
                                onInsertModule={handleInsertModule}
                                currentModule={currentModule}
                                completedModules={completedModules}
                                moduleCompletionLoading={moduleCompletionLoading}
                                userId={user?.id}
                                learningPathId={currentPath.id}
                                onQuizComplete={() => {
                                    refreshProgressData();
                                }}
                                isTeamLearningPath={isTeamContext}
                                isTeamLead={isTeamLead}
                                isGeneratingModules={isGeneratingModules}
                                generatingModules={generatingModules}
                            />
                        </motion.div>

                        <AnimatePresence>
                            {completedModules.size > 0 && (
                                <motion.div
                                    className="bg-gradient-to-r from-primary to-accent text-white rounded-xl shadow-lg p-6"
                                    initial={{opacity: 0, y: 20}}
                                    animate={{opacity: 1, y: 0}}
                                    exit={{opacity: 0, y: -20}}
                                >
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex-grow">
                                            <h3 className="font-display font-bold text-xl">
                                                {isPathComplete ? "Congrats!" : "Great Progress!"}
                                            </h3>
                                            <p className="text-sm opacity-90 mt-1">
                                                {isPathComplete
                                                    ? "You've finished your path!"
                                                    : `You have completed ${completedModules.size} ${completedModules.size === 1 ? 'module' : 'modules'}!`}
                                            </p>
                                        </div>
                                        {isPathComplete && (
                                            <Button onClick={() => setShowCertificate(true)}
                                                    className={variantStyles.success}>
                                                View Certificate
                                            </Button>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    <div className="space-y-6">
                        <ProgressTracker
                            completedModules={completedModules}
                            totalModules={modules.length}
                            currentModule={currentModule}
                        />

                        {preferences ? (
                            <GenerationDetailsCard title="Path Generation Details" icon={Dna}>
                                <GenerationDetails preferences={preferences}/>
                            </GenerationDetailsCard>
                        ) : (
                            // Show a placeholder or message indicating preferences are not available
                            <GenerationDetailsCard title="Path Generation Details" icon={Dna}>
                                <div className="p-4 text-center text-gray-500">
                                    <p className="text-sm">Generation preferences not available for this learning
                                        path.</p>
                                    <p className="text-xs mt-2 text-gray-400">This might be an older path or preferences
                                        weren't saved during generation.</p>
                                </div>
                            </GenerationDetailsCard>
                        )}
                        <LearningAnalytics
                            completedModulesCount={completedModules.size}
                            timeInvestedInPath={timeInvestedInPath}
                            questionsAnswered={userStatistics?.questions_answered || 0}
                            skillPoints={userStatistics?.skill_points || 0}
                        />
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
