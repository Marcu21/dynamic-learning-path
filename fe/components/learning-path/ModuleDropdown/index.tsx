"use client"

import {useState, memo, useCallback, useEffect, useRef} from "react"
import {motion, AnimatePresence} from "framer-motion"
import {
    ChevronDown,
    Play,
    CheckCircle,
    Clock,
    FileText,
    ExternalLink,
    CircleCheckBig,
    Brain,
    History,
    Award,
    X,
    Plus,
    Sparkles,
    Send,
    AlertTriangle,
    CircleX
} from "lucide-react"
import {Button} from "@/components/common/Button"
import {api} from "@/lib/api"
import type {QuizAttempt} from "@/types/quiz"
import QuizInterface from "@/components/learning-path/QuizInterface"
import {useChatLocationUpdater} from "@/context/ChatContext"
import {ModuleDropdownProps} from "@/components/learning-path/ModuleDropdown/types"

function ModuleDropdown({
                            module,
                            index,
                            status,
                            locked,
                            onModuleSelect,
                            onMarkComplete,
                            onInsertModule,
                            isExpanded: controlledExpanded,
                            onToggleExpanded,
                            isCompletionLoading = false,
                            userId,
                            learningPathId,
                            onQuizComplete,
                            isTeamLearningPath = false,
                            isTeamLead = false,
                        }: ModuleDropdownProps) {
    const {
        setModuleContext,
        setQuizAttemptContext,
        setReviewAnswersContext,
        setQuizContext,
        setModuleContextForce,
        setQuizContextForce,
        setLearningPathContextForce
    } = useChatLocationUpdater()
    const [internalExpanded, setInternalExpanded] = useState(false)

    const [hasAccessedContent, setHasAccessedContent] = useState(false)
    const [showConfirmationModal, setShowConfirmationModal] = useState(false)


    const [activeTab, setActiveTab] = useState<"overview" | "quiz" | "answers">("overview")
    const [showQuiz, setShowQuiz] = useState(false)
    const [quizAttempts, setQuizAttempts] = useState<QuizAttempt[]>([])
    const [loadingAttempts, setLoadingAttempts] = useState(false)
    const [selectedAttempt, setSelectedAttempt] = useState<any>(null)
    const [loadingDetails, setLoadingDetails] = useState(false)

    const [showGenerateModal, setShowGenerateModal] = useState(false)
    const [generateQuery, setGenerateQuery] = useState("")
    const [isGenerating, setIsGenerating] = useState(false)

    // Platform selection state
    const [platforms, setPlatforms] = useState<any[]>([])
    const [selectedPlatform, setSelectedPlatform] = useState<string>("")
    const [loadingPlatforms, setLoadingPlatforms] = useState(false)

    const [, setPlatformName] = useState<string | undefined>(undefined);

    const isExpanded = controlledExpanded !== undefined ? controlledExpanded : internalExpanded
    const [errors, setErrors] = useState<{ generateQuery?: string; selectedPlatform?: string }>({});


    const loadQuizAttempts = useCallback(async () => {
        if (!userId || !module.id) return
        setLoadingAttempts(true)
        try {
            const attempts = await api.getUserQuizAttemptsByModule(module.id, userId)
            setQuizAttempts(attempts)
        } catch (error) {
            setQuizAttempts([])
        } finally {
            setLoadingAttempts(false)
        }
    }, [userId, module.id])

    useEffect(() => {
        if (isExpanded && activeTab === "answers" && userId && module.id) {
            loadQuizAttempts()
        }
    }, [isExpanded, activeTab, userId, module.id, loadQuizAttempts])

    useEffect(() => {
        if (isExpanded && learningPathId && module.id) {
            setModuleContext(learningPathId, module.id)
        }
    }, [isExpanded, learningPathId, module.id, setModuleContext])

    useEffect(() => {
        if (module.platform_id) {
            const fetchPlatform = async () => {
            };
            fetchPlatform();
        } else {
            setPlatformName("N/A");
        }
    }, [module.platform_id]);

    useEffect(() => {
        if (
            activeTab === "quiz" &&
            isExpanded &&
            learningPathId &&
            module.id &&
            showQuiz &&
            quizAttempts.length > 0
        ) {
            const latestAttempt = quizAttempts[quizAttempts.length - 1]
            if (latestAttempt) {
                setQuizAttemptContext(learningPathId, module.id, latestAttempt.quiz_id, latestAttempt.id)
            }
        }
    }, [activeTab, isExpanded, learningPathId, module.id, showQuiz, quizAttempts, setQuizAttemptContext])


    useEffect(() => {
        if (activeTab === "answers" && isExpanded && learningPathId && module.id && selectedAttempt) {
            setReviewAnswersContext(learningPathId, module.id, selectedAttempt.quiz_id, selectedAttempt.id)
        }
    }, [activeTab, isExpanded, learningPathId, module.id, selectedAttempt, setReviewAnswersContext])

    useEffect(() => {
        if (!isExpanded) return
        if (!learningPathId || !module?.id) return

        if (activeTab !== "quiz" && activeTab !== "answers") {
            setModuleContextForce(learningPathId, module.id)
        }
    }, [activeTab, isExpanded, learningPathId, module?.id, setModuleContextForce])

    useEffect(() => {
        if (activeTab !== "quiz") return
        setSelectedAttempt(null)
        setShowQuiz(true)
        if (isExpanded && learningPathId && module.id) {
            const latestAttempt = quizAttempts.length > 0 ? quizAttempts[quizAttempts.length - 1] : null
            const quizId = latestAttempt ? latestAttempt.quiz_id : undefined
            setQuizContextForce(learningPathId, module.id, quizId as any)
        }
    }, [activeTab, isExpanded, learningPathId, module.id, quizAttempts, setQuizContextForce])

    const wasExpandedRef = useRef<boolean>(isExpanded)

    useEffect(() => {
        if (wasExpandedRef.current && !isExpanded) {
            setActiveTab("overview")
            setSelectedAttempt(null)
            setShowQuiz(false)

            if (learningPathId) {
                setLearningPathContextForce(learningPathId)
            }
        }
        wasExpandedRef.current = isExpanded
    }, [isExpanded, learningPathId, setLearningPathContextForce])


    const handleToggle = () => {
        if (!locked) {
            const newExpanded = !isExpanded
            if (onToggleExpanded) {
                onToggleExpanded(newExpanded)
            } else {
                setInternalExpanded(newExpanded)
            }
        }
    }

    const proceedWithCompletion = async () => {
        try {
            await onMarkComplete(module)
            if (onToggleExpanded) {
                onToggleExpanded(false)
            } else {
                setInternalExpanded(false)
            }
        } catch (error) {
        }
    }

    const handleAccessContent = () => {
        if (module.content_url) {
            window.open(module.content_url, "_blank")
        } else {
            onModuleSelect(module)
        }
        setHasAccessedContent(true)
    }

    const handleMarkCompleteClick = () => {
        if (quizAttempts.length === 0) {
            setShowConfirmationModal(true)
        } else {
            proceedWithCompletion()
        }
    }

    const validateInputs = () => {
        const newErrors: { generateQuery?: string; selectedPlatform?: string } = {};
        if (!generateQuery.trim()) {
            newErrors.generateQuery = "Please describe what you want to learn.";
        }
        if (!selectedPlatform) {
            newErrors.selectedPlatform = "Please choose a platform.";
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleGenerateModule = async () => {
        if (isGenerating) return;

        const isValid = validateInputs();
        if (!isValid) {
            return;
        }

        setIsGenerating(true);
        try {
            if (onInsertModule) {
                await onInsertModule(index, generateQuery.trim(), selectedPlatform);
            }

            setShowGenerateModal(false);
            setGenerateQuery("");
            setSelectedPlatform("");
            setErrors({});

        } catch (error) {
        } finally {
            setIsGenerating(false);
        }
    };

    const ErrorMessage = ({message, className = ""}: { message?: string, className?: string }) => {
        if (!message) return null;
        return (
            <motion.div
                initial={{opacity: 0, y: -5}}
                animate={{opacity: 1, y: 0}}
                exit={{opacity: 0}}
                className={`mt-1 flex items-center text-sm text-red-600 space-x-1.5 ml-1 ${className}`}
            >
                <AlertTriangle className="w-4 h-4"/>
                <span>{message}</span>
            </motion.div>
        );
    };


    const handleTabChange = (tab: "overview" | "quiz" | "answers") => {
        setActiveTab(tab)

        if (tab === "quiz") {
            setSelectedAttempt(null)
            setShowQuiz(true)

            if (isExpanded && learningPathId && module.id) {
                const latestAttempt = quizAttempts.length > 0 ? quizAttempts[quizAttempts.length - 1] : null
                const quizId = latestAttempt ? latestAttempt.quiz_id : undefined

                setQuizContextForce(learningPathId, module.id, quizId as any)
            }
            return
        }

        if (tab === "answers" && isExpanded && learningPathId && module.id) {
            const latestAttempt = quizAttempts.length > 0 ? quizAttempts[quizAttempts.length - 1] : null
            if (latestAttempt) {
                setReviewAnswersContext(learningPathId, module.id, latestAttempt.quiz_id, latestAttempt.id)
            } else {
                setReviewAnswersContext(learningPathId, module.id, undefined as any, undefined as any)
            }
            if (quizAttempts.length === 0) loadQuizAttempts()
            return
        }

        if (tab === "overview") {
            setSelectedAttempt(null)
            setShowQuiz(false)
            if (isExpanded && learningPathId && module.id) {
                setModuleContextForce(learningPathId, module.id)
            }
        }
    }


    const loadAttemptDetails = useCallback(async (attempt: QuizAttempt) => {
        setLoadingDetails(true)
        try {
            // Fetch detailed attempt information including answers
            const detailedAttempt = await api.getQuizAttemptDetails(attempt.id)
            setSelectedAttempt(detailedAttempt)
            setActiveTab("answers") // Switch to answers tab to show the details
        } catch (error) {
            setSelectedAttempt(null)
        } finally {
            setLoadingDetails(false)
        }
    }, [])

    const closeAttemptDetails = () => {
        setSelectedAttempt(null)
    }

    const handleQuizComplete = () => {
        // Always reload quiz attempts when a quiz is completed, regardless of current tab
        loadQuizAttempts()
        if (onQuizComplete) {
            onQuizComplete()
        }
    }

    const getStatusColor = () => {
        switch (status) {
            case "completed":
                return "bg-success-light border-success text-success-dark"
            case "current":
                return "bg-primary-light border-primary text-primary-dark"
            default:
                return locked
                    ? "bg-neutral-accent-light border-neutral-secondary text-neutral-secondary-light"
                    : "bg-white border-neutral-secondary text-neutral-dark hover:border-primary hover:bg-primary-light/10"
        }
    }

    const getIcon = () => {
        if (status === "completed") {
            return <CheckCircle className="w-5 h-5 text-success"/>
        }
        if (status === "current") {
            return <Play className="w-4 h-4 text-primary"/>
        }
        return <span className="font-sans text-neutral-secondary-light font-bold">{index + 1}</span>
    }

    const formatTimestamp = (timestamp: string) => {
        try {
            const date = new Date(timestamp)
            const dateOptions: Intl.DateTimeFormatOptions = {
                timeZone: "Etc/GMT-2",
                year: "numeric",
                month: "long",
                day: "numeric"
            }
            const timeOptions: Intl.DateTimeFormatOptions = {
                timeZone: "Etc/GMT-2",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }
            return {
                date: date.toLocaleDateString("en-GB", dateOptions),
                time: date.toLocaleTimeString("en-GB", timeOptions),
                full: date.toLocaleString("en-GB", {...dateOptions, ...timeOptions})
            }
        } catch (error) {
            return {date: "Invalid Date", time: "Invalid Time", full: "Invalid Date"}
        }
    }

    // Load platforms when modal opens
    const loadPlatforms = useCallback(async () => {
        if (!learningPathId) return

        setLoadingPlatforms(true)
        try {
            const preferences = await api.getLearningPathPreferences(learningPathId)
            // Convert platform names to platform objects for the dropdown
            const platformObjects = (preferences.preferred_platforms || []).map((platformName: string, index: number) => ({
                id: index + 1, // Use index as ID since we only have names
                name: platformName
            }))
            setPlatforms(platformObjects)
        } catch (error) {
            setPlatforms([])
        } finally {
            setLoadingPlatforms(false)
        }
    }, [learningPathId])

    // Load platforms when modal opens
    useEffect(() => {
        if (showGenerateModal && learningPathId) {
            loadPlatforms()
        }
    }, [showGenerateModal, learningPathId, loadPlatforms])

    // Reset form when modal closes
    useEffect(() => {
        if (!showGenerateModal) {
            setGenerateQuery("")
            setSelectedPlatform("")
            setPlatforms([])
        }
    }, [showGenerateModal])

    return (
        <>
            <motion.div
                className="mb-4"
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: index * 0.1}}
            >
                <motion.div
                    className={`border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 ${getStatusColor()}`}
                    onClick={handleToggle}
                    whileHover={!locked ? {scale: 1.02} : {}}
                    whileTap={!locked ? {scale: 0.98} : {}}
                >
                    <div className="flex items-start justify-between gap-4">
                        <div
                            className="flex items-center space-x-3 flex-1 min-w-0 max-w-[65%] sm:max-w-[calc(100%-13rem)]">
                            <div className="w-6 h-6 flex-shrink-0 flex items-center justify-center">{getIcon()}</div>
                            <div className="flex-1 min-w-0">
                                <h3 className="font-display font-semibold text-lg leading-tight break-words line-clamp-2">
                                    {module.title}
                                </h3>
                            </div>
                        </div>

                        {module.is_inserted && (
                            <div className="flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-amber-600"/>
                            </div>
                        )}

                        <div className="flex items-center space-x-3 flex-shrink-0">
                            <div className="flex items-center space-x-2 text-xs">
                                <div className="font-sans opacity-80 hidden sm:flex items-center">
                                    <Clock className="w-3 h-3 mr-1"/>
                                    {module.duration}m
                                </div>
                                <div
                                    className="font-sans opacity-80 hidden sm:block capitalize">{module.difficulty}</div>
                            </div>
                            {!locked && (
                                <motion.div animate={{rotate: isExpanded ? 180 : 0}} transition={{duration: 0.2}}>
                                    <ChevronDown className="w-5 h-5"/>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </motion.div>

                <AnimatePresence>
                    {isExpanded && !locked && (
                        <motion.div
                            initial={{opacity: 0, height: 0}}
                            animate={{opacity: 1, height: "auto"}}
                            exit={{opacity: 0, height: 0}}
                            transition={{duration: 0.3, ease: "easeInOut"}}
                            className="overflow-hidden"
                        >
                            <div className="bg-white rounded-xl shadow-lg p-8 mt-2 border relative">
                                <div
                                    className="flex items-center justify-between mb-6 bg-neutral-accent-light p-1 rounded-lg">
                                    <div className="flex space-x-1">
                                        <button
                                            onClick={() => handleTabChange("overview")}
                                            className={`flex items-center px-4 py-2 rounded-md transition-all ${
                                                activeTab === "overview"
                                                    ? "bg-white text-primary shadow-sm font-bold"
                                                    : "text-neutral-secondary-light hover:text-neutral-dark"
                                            }`}
                                        >
                                            <FileText className="w-4 h-4 mr-2"/>
                                            <span className="capitalize">Overview</span>
                                        </button>
                                        <button
                                            onClick={() => handleTabChange("quiz")}
                                            className={`flex items-center px-4 py-2 rounded-md transition-all ${
                                                activeTab === "quiz"
                                                    ? "bg-white text-primary shadow-sm font-bold"
                                                    : "text-neutral-secondary-light hover:text-neutral-dark"
                                            }`}
                                        >
                                            <Brain className="w-4 h-4 mr-2"/>
                                            <span className="capitalize">Quiz</span>
                                        </button>
                                        {userId && module.id && (
                                            <button
                                                onClick={() => handleTabChange("answers")}
                                                className={`flex items-center px-4 py-2 rounded-md transition-all ${
                                                    activeTab === "answers"
                                                        ? "bg-white text-primary shadow-sm font-bold"
                                                        : "text-neutral-secondary-light hover:text-neutral-dark"
                                                }`}
                                            >
                                                <History className="w-4 h-4 mr-2"/>
                                                <span className="capitalize">Answers</span>
                                                {quizAttempts.length > 0 && (
                                                    <span
                                                        className="ml-1 bg-primary text-white text-xs rounded-full px-2 py-0.5">
                                                        {quizAttempts.length}
                                                    </span>
                                                )}
                                            </button>
                                        )}
                                    </div>

                                    {module.is_inserted && (
                                        <div
                                            className="flex items-center gap-1.5 text-md text-amber-700 font-bold px-2">
                                            <Sparkles className="w-4 h-4 text-amber-600"/>
                                            <span>Inserted</span>
                                        </div>
                                    )}
                                </div>

                                <AnimatePresence mode="wait">
                                    {activeTab === "overview" && (
                                        <motion.div
                                            key="overview"
                                            initial={{opacity: 0, x: -20}}
                                            animate={{opacity: 1, x: 0}}
                                            exit={{opacity: 0, x: 20}}
                                            transition={{duration: 0.3}}
                                            className="mb-8 space-y-6"
                                        >
                                            <div className="flex gap-6 flex-wrap">
                                                <div>
                                                    <span
                                                        className="font-bold text-neutral-dark text-base">Duration:</span>{" "}
                                                    <span
                                                        className="text-neutral-dark text-base">{module.duration} minutes</span>
                                                </div>
                                                <div>
                                                    <span
                                                        className="font-bold text-neutral-dark text-base">Difficulty:</span>{" "}
                                                    <span
                                                        className="text-neutral-dark capitalize text-base">{module.difficulty}</span>
                                                </div>
                                                <div>
                                                    <span
                                                        className="font-bold text-neutral-dark text-base">Platform:</span>{" "}
                                                    <span
                                                        className="text-neutral-dark capitalize text-base">{module.platform_name || 'Unknown'}</span>
                                                </div>
                                            </div>

                                            <div>
                                                <h3 className="text-lg font-bold text-neutral-dark mb-3">Learning
                                                    Objectives</h3>
                                                {module.learning_objectives && module.learning_objectives.length > 0 ? (
                                                    <ul className="list-disc list-inside space-y-1 text-neutral-dark">
                                                        {module.learning_objectives.map((objective, index) => (
                                                            <li key={index} className="text-base text-neutral-dark">
                                                                {objective}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                ) : (
                                                    <ul className="list-disc list-inside space-y-1 text-neutral-dark">
                                                        <li className="text-sm text-neutral-dark">Understand the key
                                                            concepts
                                                        </li>
                                                        <li className="text-sm text-neutral-dark">Apply practical
                                                            skills
                                                        </li>
                                                        <li className="text-sm text-neutral-dark">Complete hands-on
                                                            exercises
                                                        </li>
                                                    </ul>
                                                )}
                                            </div>

                                            <div>
                                                <h3 className="text-lg font-bold text-neutral-dark mb-3">Description</h3>
                                                <p className="text-neutral-dark text-base mb-4">{module.description}</p>
                                                {status !== "completed" && (
                                                    <p className="text-neutral-secondary-light">
                                                        Ready to get started? Click the link below to access the
                                                        learning material.
                                                    </p>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}

                                    {activeTab === "quiz" && (
                                        <motion.div
                                            key="quiz"
                                            initial={{opacity: 0, x: -20}}
                                            animate={{opacity: 1, x: 0}}
                                            exit={{opacity: 0, x: 20}}
                                            transition={{duration: 0.3}}
                                            className="mb-8"
                                        >
                                            {showQuiz && userId && module.id ? (
                                                <QuizInterface
                                                    moduleId={module.id}
                                                    userId={userId}
                                                    onClose={() => setShowQuiz(false)}
                                                    learningPathId={learningPathId}
                                                    onQuizComplete={handleQuizComplete}
                                                />
                                            ) : (
                                                <div className="text-center py-8">
                                                    <Brain className="w-16 h-16 text-primary mx-auto mb-4"/>
                                                    <h3 className="text-xl font-bold text-neutral-dark mb-2">Test Your
                                                        Knowledge</h3>
                                                    <p className="text-neutral-secondary-light mb-6">
                                                        Take a quiz to reinforce what you've learned in this module and
                                                        track your progress.
                                                    </p>
                                                    {userId && module.id ? (
                                                        <Button onClick={() => setShowQuiz(true)} variant="primary"
                                                                className="px-6">
                                                            <Brain className="w-4 h-4 mx-auto" strokeWidth={2.5}/>
                                                            Take Quiz
                                                        </Button>
                                                    ) : (
                                                        <p className="text-sm text-neutral-secondary-light">
                                                            Quiz functionality requires a valid user ID and module ID.
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </motion.div>
                                    )}

                                    {activeTab === "answers" && (
                                        <motion.div
                                            key="answers"
                                            initial={{opacity: 0, x: -20}}
                                            animate={{opacity: 1, x: 0}}
                                            exit={{opacity: 0, x: 20}}
                                            transition={{duration: 0.3}}
                                            className="mb-8"
                                        >
                                            <h3 className="text-lg font-bold text-neutral-dark mb-3">Your Quiz
                                                History</h3>
                                            {loadingAttempts ? (
                                                <div className="text-center py-8">
                                                    <motion.div
                                                        className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto"
                                                        animate={{rotate: 360}}
                                                        transition={{
                                                            duration: 1,
                                                            repeat: Number.POSITIVE_INFINITY,
                                                            ease: "linear"
                                                        }}
                                                    />
                                                    <p className="mt-2 text-neutral-secondary-light">Loading quiz
                                                        attempts...</p>
                                                </div>
                                            ) : quizAttempts.length === 0 ? (
                                                <div className="text-center py-8">
                                                    <History
                                                        className="w-16 h-16 text-neutral-secondary-light mx-auto mb-4"/>
                                                    <p className="text-neutral-secondary-light">You haven't taken any
                                                        quizzes for this module yet.</p>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    {quizAttempts.map((attempt, index) => (
                                                        <div
                                                            key={attempt.id}
                                                            className="border border-neutral-secondary rounded-lg p-4 hover:shadow-md transition-shadow"
                                                        >
                                                            <div className="flex items-center justify-between mb-3">
                                                                <div className="flex items-center space-x-3">
                                                                    <div
                                                                        className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                                                            attempt.passed ? "bg-success-light text-success" : "bg-red-100 text-red-600"
                                                                        }`}
                                                                    >
                                                                        {attempt.passed ? <Award className="w-4 h-4"/> :
                                                                            <CircleX className="w-4 h-4"/>}
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="font-semibold text-neutral-dark">Attempt
                                                                            #{index + 1}</h4>
                                                                        <p className="text-sm text-neutral-secondary-light">
                                                                            {formatTimestamp(attempt.started_at).date} at{" "}
                                                                            {formatTimestamp(attempt.started_at).time}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div className="text-right">
                                                                    <div
                                                                        className="text-lg font-bold text-neutral-dark">
                                                                        {Math.round(attempt.score)}%
                                                                    </div>
                                                                    <div
                                                                        className="text-sm text-neutral-secondary-light">
                                                                        {attempt.earned_points}/{attempt.total_points} points
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {attempt.time_taken && (
                                                                <div
                                                                    className="flex items-center text-sm text-neutral-secondary-light mb-3">
                                                                    <Clock className="w-4 h-4 mr-1"/>
                                                                    Time taken: {Math.floor(attempt.time_taken / 60)}:
                                                                    {(attempt.time_taken % 60).toString().padStart(2, "0")}
                                                                </div>
                                                            )}

                                                            <div className="flex justify-between items-center">
                                                                <div
                                                                    className={`px-3 py-1 text-xs font-medium rounded-full
                                   ${attempt.passed ? "bg-green-100 text-black border border-green-700" :
                                                                        "bg-red-100 text-black border border-red-700"}
                                   `}>
                                                                    {attempt.passed ? "Passed" : "Failed"}
                                                                </div>
                                                                <div className="flex items-center space-x-2">
                                                                    {attempt.passed && attempt.skill_points_awarded && (
                                                                        <div
                                                                            className="flex items-center text-xs text-green-600 font-medium">
                                                                            <Award className="w-3 h-3 mr-1"/>
                                                                            +30 SP
                                                                        </div>
                                                                    )}
                                                                    <Button
                                                                        variant="hollow"
                                                                        onClick={() => {
                                                                            loadAttemptDetails(attempt)
                                                                        }}
                                                                    >
                                                                        View Details
                                                                    </Button>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* <<< MODIFICATION START >>> */}
                                <div
                                    className="flex justify-between items-center pt-6 border-t border-neutral-secondary">
                                    <div className="flex items-center text-sm font-sans text-neutral-dark">
                                        <Clock className="w-4 h-4 mr-1"/>
                                        {module.duration} minutes
                                    </div>
                                    <div className="flex gap-3 flex-wrap items-center">
                                        <Button
                                            onClick={handleAccessContent}
                                            variant="primary"
                                            className="px-1 font-bold">
                                            <ExternalLink className="w-4 h-4 mr-1" strokeWidth={2.5}/>
                                            Access Content
                                        </Button>
                                        {status !== "completed" && (
                                            <Button
                                                onClick={handleMarkCompleteClick}
                                                variant="success"
                                                className={`px-1 font-bold transition-opacity ${isCompletionLoading || !hasAccessedContent ? '!opacity-50 cursor-not-allowed' : ''}`}
                                                disabled={isCompletionLoading || !hasAccessedContent}
                                                title={!hasAccessedContent ? "You must access the content first" : "Mark as complete"}
                                            >

                                                {isCompletionLoading ? (
                                                    <>
                                                        <motion.div
                                                            className="w-5 h-5 mr-2 border-2 border-white border-t-transparent rounded-full"
                                                            animate={{rotate: 360}}
                                                            transition={{
                                                                duration: 1,
                                                                repeat: Number.POSITIVE_INFINITY,
                                                                ease: "linear"
                                                            }}
                                                        />
                                                        Saving...
                                                    </>
                                                ) : (
                                                    <>
                                                        <CircleCheckBig className="w-5 h-5 mr-1" strokeWidth={2.5}/>
                                                        Mark as Complete
                                                    </>
                                                )}
                                            </Button>
                                        )}
                                        {onInsertModule && (!isTeamLearningPath || isTeamLead) && (
                                            <motion.button
                                                onClick={() => setShowGenerateModal(true)}
                                                className="relative w-10 h-10 bg-gray-200 text-gray-600 rounded-full flex items-center justify-center transition-colors duration-300 group overflow-hidden"
                                                whileTap={{scale: 0.95}}
                                                title="Generate new module"
                                            >
                                                <motion.div
                                                    className="absolute inset-0 w-full h-full bg-gray-300/70 rounded-full"
                                                    initial={{scale: 0}}
                                                    whileHover={{scale: 1}}
                                                    transition={{duration: 0.3, ease: "easeOut"}}
                                                />
                                                <div
                                                    className="absolute w-[88%] h-[88%] bg-gray-200 group-hover:bg-gray-100 rounded-full transition-colors duration-300"/>
                                                <motion.div
                                                    className="relative z-10"
                                                    whileHover={{rotate: 90}}
                                                    transition={{duration: 0.25, ease: "easeOut"}}
                                                >
                                                    <Plus
                                                        className="w-5 h-5 text-gray-700 group-hover:text-gray-700 transition-colors"
                                                        strokeWidth={2.5}/>
                                                </motion.div>
                                            </motion.button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <AnimatePresence>
                    {showConfirmationModal && (
                        <motion.div
                            initial={{opacity: 0}}
                            animate={{opacity: 1}}
                            exit={{opacity: 0}}
                            transition={{duration: 0.1, ease: "easeOut"}}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                            onClick={() => setShowConfirmationModal(false)}
                        >
                            <motion.div
                                initial={{scale: 0.95, opacity: 0}}
                                animate={{scale: 1, opacity: 1}}
                                exit={{scale: 0.95, opacity: 0}}
                                transition={{
                                    duration: 0.15,
                                    ease: "easeOut"
                                }}
                                className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden"
                                onClick={(e) => e.stopPropagation()}
                            >
                                {/* Header */}
                                <div className="bg-white px-8 pt-8 pb-6 text-center relative">
                                  <div className="absolute top-4 right-4">
                                    <button
                                      onClick={() => setShowConfirmationModal(false)}
                                      className="text-neutral-500 hover:text-neutral-800 transition-colors"
                                      title="Close"
                                    >
                                      <X className="w-6 h-6" />
                                    </button>
                                  </div>

                                  <motion.div
                                    initial={{ scale: 0.8 }}
                                    animate={{ scale: 1 }}
                                    transition={{ duration: 0.1, ease: "easeOut" }}
                                    className="w-20 h-20 bg-gradient-to-br from-amber-300 to-orange-400 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg"
                                  >
                                    <AlertTriangle className="w-10 h-10 text-white" />
                                  </motion.div>

                                  <motion.h3
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.1, delay: 0.05 }}
                                    className="text-2xl font-bold text-neutral-dark mb-4 sm:mb-5"
                                  >
                                    Complete Module Without Quiz?
                                  </motion.h3>

                                  <div className="text-center mb-8">
                                    <p className="text-neutral-dark">
                                      We recommend taking the quiz to test your understanding and get the most out of this module.
                                    </p>
                                  </div>

                                    {/* Action buttons */}
                                    <div className="flex flex-col-reverse sm:flex-row gap-4 mt-2 pt-1">
                                        <Button
                                            variant="primary"
                                            onClick={() => {
                                                handleTabChange("quiz");
                                                setShowConfirmationModal(false);
                                            }}
                                            className="flex-1 font-semibold bg-gradient-to-r from-primary to-blue-700 hover:from-primary-dark hover:to-blue-700 border-0 text-white"
                                        >
                                            <Brain className="w-4 h-4 mr-1"/>
                                            Take the Quiz
                                        </Button>

                                        <Button
                                            variant="hollow"
                                            onClick={() => {
                                                proceedWithCompletion();
                                                setShowConfirmationModal(false);
                                            }}
                                            className="flex-1 font-semibold text-primary border-primary hover:bg-primary/10"
                                        >
                                            <CircleCheckBig className="w-4 h-4 mr-1"/>
                                            Complete Anyway
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <AnimatePresence>
                    {selectedAttempt && (
                        <motion.div
                            initial={{opacity: 0}}
                            animate={{opacity: 1}}
                            exit={{opacity: 0}}
                            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                            onClick={closeAttemptDetails}
                        >
                            <motion.div
                                initial={{scale: 0.9, opacity: 0}}
                                animate={{scale: 1, opacity: 1}}
                                exit={{scale: 0.9, opacity: 0}}
                                className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <div
                                    className="flex items-center justify-between p-6 border-b border-neutral-secondary">
                                    <div>
                                        <h3 className="text-xl font-bold text-neutral-dark">Quiz Attempt Details</h3>
                                        <p className="text-md text-neutral-secondary-light">
                                            {selectedAttempt && formatTimestamp(selectedAttempt.started_at).full}
                                        </p>
                                    </div>
                                    <button onClick={closeAttemptDetails}
                                            className="text-neutral-secondary-light hover:text-neutral-dark">
                                        <X className="w-6 h-6"/>
                                    </button>
                                </div>

                                <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                                    {loadingDetails ? (
                                        <div className="text-center py-8">
                                            <motion.div
                                                className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto"
                                                animate={{rotate: 360}}
                                                transition={{
                                                    duration: 1,
                                                    repeat: Number.POSITIVE_INFINITY,
                                                    ease: "linear"
                                                }}
                                            />
                                            <p className="mt-2 text-neutral-secondary-light">Loading attempt
                                                details...</p>
                                        </div>
                                    ) : selectedAttempt ? (
                                        <div className="space-y-6">
                                            <div className="bg-neutral-accent-light rounded-lg p-4">
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                    <div className="flex flex-col items-center">
                                                        <p className="text-lg text-neutral-dark font-bold">Score</p>
                                                        <p className="text-lg font-medium text-neutral-secondary-light">
                                                            {Math.round(selectedAttempt.score)}%
                                                        </p>
                                                    </div>

                                                    <div className="flex flex-col items-center">
                                                        <p className="text-lg text-neutral-dark font-bold">Points</p>
                                                        <p className="text-lg font-medium text-neutral-secondary-light">
                                                            {selectedAttempt.earned_points}/{selectedAttempt.total_points}
                                                        </p>
                                                    </div>

                                                    <div className="flex flex-col items-center">
                                                        <p className="text-lg text-neutral-dark font-bold">Status</p>
                                                        <div
                                                            className={`px-3 py-1 text-sm font-medium rounded-full
                                  ${selectedAttempt.passed ? "bg-green-100 text-black border border-green-700" :
                                                                "bg-red-100 text-black border border-red-700"}
                                  `}>
                                                            {selectedAttempt.passed ? "Passed" : "Failed"}
                                                        </div>
                                                    </div>

                                                    {selectedAttempt.time_taken && (
                                                        <div className="flex flex-col items-center">
                                                            <p className="text-lg text-neutral-dark font-bold">Time</p>
                                                            <p className="text-lg font-medium text-neutral-secondary-light">
                                                                {Math.floor(selectedAttempt.time_taken / 60)}:
                                                                {(selectedAttempt.time_taken % 60).toString().padStart(2, "0")}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <div>
                                                <h4 className="text-lg font-semibold text-neutral-dark mb-4">Your
                                                    Answers</h4>
                                                <div className="space-y-4">
                                                    {selectedAttempt.answers &&
                                                        selectedAttempt.answers.map((answer: any, index: number) => (
                                                            <div
                                                                key={index}
                                                                className={`border rounded-lg p-4 ${
                                                                    answer.is_correct ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"
                                                                }`}
                                                            >
                                                                <div className="flex items-start justify-between mb-3">
                                                                    <h5 className="font-semibold text-neutral-dark flex-1">
                                                                        Question {index + 1}: {answer.question_text || `Question ${index + 1}`}
                                                                    </h5>
                                                                    <div className="flex items-center space-x-2 ml-4">
                                                                        {answer.is_correct ? (
                                                                            <CheckCircle
                                                                                className="w-5 h-5 text-green-600"/>
                                                                        ) : (
                                                                            <CircleX className="w-5 h-5 text-red-600"/>
                                                                        )}
                                                                        <span
                                                                            className="text-sm font-medium">{answer.points_earned} pts</span>
                                                                    </div>
                                                                </div>

                                                                <div className="space-y-3">
                                                                    <div>
                                                                        <p className="text-sm font-bold text-neutral-secondary-light mb-1">Your
                                                                            Answer</p>
                                                                        <p className={`p-3 rounded border ${
                                                                            answer.is_correct
                                                                                ? "text-[#10652F] bg-white border-green-500"
                                                                                : "text-[#AB1C1C] bg-white border-red-500"
                                                                        }`}>
                                                                            {answer.user_answer || answer.answer_text || "No answer provided"}
                                                                        </p>
                                                                    </div>

                                                                    {!answer.is_correct && answer.correct_answer && (
                                                                        <div>
                                                                            <p className="text-sm font-bold text-neutral-secondary-light mb-1">Correct
                                                                                Answer</p>
                                                                            <p className="text-[#10652F] bg-white p-3 rounded border border-green-500">
                                                                                {answer.correct_answer}
                                                                            </p>
                                                                        </div>
                                                                    )}

                                                                    {answer.ai_feedback && (
                                                                        <div>
                                                                            <p className="text-sm font-bold text-neutral-secondary-light mb-1">Feedback</p>
                                                                            <p className="text-sm text-neutral-dark bg-white p-2 rounded border">
                                                                                {answer.ai_feedback}
                                                                            </p>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-8">
                                            <X className="w-16 h-16 text-red-500 mx-auto mb-4"/>
                                            <p className="text-neutral-secondary-light">Failed to load attempt details.
                                                Please try again.</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

            <AnimatePresence>
                {showGenerateModal && (
                    <motion.div
                        initial={{opacity: 0}}
                        animate={{opacity: 1}}
                        exit={{opacity: 0}}
                        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                        onClick={() => !isGenerating && setShowGenerateModal(false)}
                    >
                        <motion.div
                            initial={{scale: 0.9, opacity: 0}}
                            animate={{scale: 1, opacity: 1}}
                            exit={{scale: 0.9, opacity: 0}}
                            className="bg-white rounded-xl shadow-xl max-w-2xl w-full"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between p-6 border-b border-neutral-secondary">
                                <div className="flex items-center space-x-3">
                                    <div
                                        className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                                        <Sparkles className="w-5 h-5 text-white"/>
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-bold text-neutral-dark">Generate New Module</h3>
                                    </div>
                                </div>
                                {!isGenerating && (
                                    <button
                                        onClick={() => setShowGenerateModal(false)}
                                        className="text-neutral-secondary-light hover:text-neutral-dark"
                                    >
                                        <X className="w-6 h-6"/>
                                    </button>
                                )}
                            </div>

                            <div className="p-6">
                                <div className="space-y-4">
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                        <div className="flex items-start space-x-3">
                                            <Sparkles className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0"/>
                                            <div>
                                                <h4 className="font-bold text-neutral-dark mb-1">AI-Powered Module
                                                    Generation</h4>
                                                <p className="text-md text-neutral-dark">
                                                    Got an idea? Turn it into a learning module with a single click.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-neutral-dark mb-2">
                                            What would you like to learn?
                                        </label>
                                        <textarea
                                            value={generateQuery}
                                            onChange={(e) => {
                                                setGenerateQuery(e.target.value);
                                                if (errors.generateQuery) setErrors(prev => ({
                                                    ...prev,
                                                    generateQuery: undefined
                                                }));
                                            }}
                                            placeholder="e.g., Advanced React hooks..."
                                            className={`w-full h-32 px-4 py-3 border text-md border-neutral-secondary rounded-lg resize-none focus:outline-none focus:ring-2 focus:border-transparent ${errors.generateQuery ? 'border-red-500 focus:ring-red-500' : 'focus:ring-primary'}`}
                                            disabled={isGenerating}
                                        />
                                        <ErrorMessage
                                            message={errors.generateQuery}
                                            className="!mt-0"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-bold text-neutral-dark mb-2">
                                            Choose Platform
                                        </label>
                                        {loadingPlatforms ? (
                                            <div
                                                className="flex items-center justify-center p-4 border border-neutral-secondary rounded-lg">
                                                <motion.div
                                                    className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full mr-2"
                                                    animate={{rotate: 360}}
                                                    transition={{
                                                        duration: 1,
                                                        repeat: Number.POSITIVE_INFINITY,
                                                        ease: "linear"
                                                    }}
                                                />
                                                <span className="text-sm text-neutral-secondary-light">Loading platforms...</span>
                                            </div>
                                        ) : (
                                            <>
                                                <select
                                                    value={selectedPlatform}
                                                    onChange={(e) => {
                                                        setSelectedPlatform(e.target.value);
                                                        if (errors.selectedPlatform) setErrors(prev => ({
                                                            ...prev,
                                                            selectedPlatform: undefined
                                                        }));
                                                    }}
                                                    className={`w-full px-4 py-3 border border-neutral-secondary rounded-lg focus:outline-none focus:ring-2 focus:border-transparent ${errors.selectedPlatform ? 'border-red-500 focus:ring-red-500' : 'focus:ring-primary'}`}
                                                    disabled={isGenerating}
                                                >
                                                    <option value="">Choose platform</option>
                                                    {platforms.map((platform) => (
                                                        <option key={platform.id} value={platform.name}>
                                                            {platform.name}
                                                        </option>
                                                    ))}
                                                </select>
                                                <ErrorMessage
                                                    message={errors.selectedPlatform}
                                                    className="!mt-2"
                                                />
                                            </>
                                        )}
                                    </div>

                                    <div className="flex justify-end space-x-3 pt-4">
                                        <Button onClick={() => setShowGenerateModal(false)} variant="hollow"
                                                disabled={isGenerating}>
                                            <span className="font-bold">Cancel</span>
                                        </Button>
                                        <Button
                                            onClick={handleGenerateModule}
                                            variant="primary"
                                            disabled={isGenerating}
                                            className="px-4"
                                        >
                                            {isGenerating ? (
                                                <>
                                                    <motion.div
                                                        className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full"
                                                        animate={{rotate: 360}}
                                                        transition={{
                                                            duration: 1,
                                                            repeat: Number.POSITIVE_INFINITY,
                                                            ease: "linear"
                                                        }}
                                                    />
                                                    <span className="font-bold">Generating...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Send className="w-4 h-4 mr-0.6"/>
                                                    <span className="font-bold">Generate Module</span>
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    )
}

export default memo(ModuleDropdown);