"use client";

import {useState, useEffect, useCallback} from "react";
import {motion} from "framer-motion";
import {
    CheckCircle,
    XCircle,
    Clock,
    Award,
    Brain,
    ArrowRight,
    ArrowLeft,
    Play,
    RotateCcw,
    Sparkles,
    Target,
    FileText,
} from "lucide-react";
import {Button} from "@/components/common/Button";
import {api} from "@/lib/api";
import type {QuizForTaking, QuizResult, QuizAttempt} from "@/types/quiz";
import {useChatLocationUpdater} from '@/context/ChatContext';
import {QuizInterfaceProps, QuizState} from "@/components/learning-path/QuizInterface/types";

// Get option text
const getOptionText = (option: any): string => {
    if (typeof option === 'string') {
        return option;
    }
    if (typeof option === 'object' && option !== null) {
        return option.text || option.label || String(option);
    }
    return String(option);
};

// Get option value
const getOptionValue = (option: any): string => {
    if (typeof option === 'string') {
        return option;
    }
    if (typeof option === 'object' && option !== null) {
        return option.value || option.text || option.label || String(option);
    }
    return String(option);
};

// Display difficulty as a user-friendly string
export function getDifficultyLabel(difficulty: any) {
    if (!difficulty) return '';

    if (typeof difficulty === 'string') {
        const parts = difficulty.split('.');
        return parts.length > 1 ? parts[1].toLowerCase() : difficulty.toLowerCase();
    }
    return String(difficulty).toLowerCase();
}

const GeneratingQuizLoader = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const steps = [
        {icon: Brain, text: "Analyzing module content..."},
        {icon: Sparkles, text: "Generating diverse questions..."},
        {icon: Target, text: "Calibrating difficulty..."},
        {icon: CheckCircle, text: "Finalizing your quiz..."},
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep((prev) => (prev + 1) % steps.length);
        }, 2000);
        return () => clearInterval(interval);
    }, [steps.length]);

    return (
        <div className="flex flex-col items-center justify-center p-8">
            <div className="relative mb-8">
                <motion.div
                    animate={{scale: [1, 1.1, 1], rotate: [0, 5, -5, 0]}}
                    transition={{duration: 2, repeat: Infinity, ease: "easeInOut"}}
                    className="w-20 h-20 bg-gradient-to-br from-primary to-primary-dark rounded-full flex items-center justify-center shadow-lg"
                >
                    <Brain className="w-10 h-10 text-white"/>
                </motion.div>
            </div>

            <div className="w-full max-w-md space-y-4 mb-8">
                {steps.map((step, index) => {
                    const Icon = step.icon;
                    const isActive = index === currentStep;
                    return (
                        <motion.div
                            key={index}
                            className={`flex items-center space-x-4 p-3 rounded-lg transition-all duration-500 ${
                                isActive ? "bg-primary-light border border-primary" : "bg-neutral-accent-light"
                            }`}
                            animate={{scale: isActive ? 1.05 : 1, opacity: isActive ? 1 : 0.6}}
                        >
                            <motion.div
                                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                    isActive ? "bg-primary text-white" : "bg-neutral-secondary text-neutral-dark"
                                }`}
                                animate={isActive ? {rotate: 360} : {}}
                                transition={{duration: 1, ease: "linear"}}
                            >
                                <Icon className="w-4 h-4"/>
                            </motion.div>
                            <p className={`font-medium ${isActive ? "text-primary-dark" : "text-neutral-dark"}`}>
                                {step.text}
                            </p>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

const SubmittingQuizLoader = () => {
    return (
        <div className="flex flex-col items-center justify-center p-8">
            <div className="relative w-20 h-20 mb-6">
                <FileText className="w-full h-full text-primary opacity-20" strokeWidth={1}/>
                <motion.div
                    className="absolute top-0 left-0 w-full h-1 bg-primary/50 rounded-full"
                    style={{boxShadow: '0 0 8px rgba(var(--color-primary), 0.7)'}}
                    animate={{y: [4, 72, 4]}}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                        repeatType: "loop",
                    }}
                />
            </div>
            <h3 className="text-xl font-bold text-neutral-dark mb-2">Grading your answers...</h3>
            <p className="text-neutral-dark">Please wait a moment.</p>
        </div>
    );
};

export default function QuizInterface({moduleId, userId, learningPathId, onClose, onQuizComplete}: QuizInterfaceProps) {
    const {setQuizContext, setQuizAttemptContext} = useChatLocationUpdater();
    const [quizState, setQuizState] = useState<QuizState>("checking_status");
    const [quiz, setQuiz] = useState<QuizForTaking | null>(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<{ [questionId: number]: string }>({});
    const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
    const [results, setResults] = useState<QuizResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [quizUnavailable] = useState(false);

    const MAX_RETRIES = 5;
    const RETRY_DELAY = 4000; // 4 seconds


    const pollForQuiz = useCallback(async (retries = 10, delay = 2000) => {
        for (let i = 0; i < retries; i++) {
            try {
                const existingQuiz = await api.getQuizForModule(moduleId);

                // Extract the actual quiz object - the API returns {quiz: {...}}
                const quizData = (existingQuiz as any)?.quiz || existingQuiz;

                // Check if quiz exists and has valid data structure
                if (quizData &&
                    typeof quizData === 'object' &&
                    quizData.questions &&
                    Array.isArray(quizData.questions) &&
                    quizData.questions.length > 0) {

                    setQuiz(quizData);
                    setQuizState("ready");
                    return; // Exit early when quiz is found
                } else {
                }
            } catch (error) {
            }

            // Don't delay on the last attempt
            if (i < retries - 1) {
                await new Promise(res => setTimeout(res, delay));
            }
        }
        setError("Quiz generation timed out. Please try again later.");
        setQuizState("ready");
    }, [moduleId]);

    const generateQuiz = useCallback(async () => {
        setQuizState("generating");
        setError(null); // Clear any previous errors

        try {
            await api.generateQuiz({module_id: moduleId, num_questions: 5});
            // Always poll for quiz availability after triggering generation
            await pollForQuiz();
        } catch (error) {

            if (retryCount < MAX_RETRIES) {
                setRetryCount(prev => prev + 1);
                setTimeout(() => generateQuiz(), RETRY_DELAY * (retryCount + 1));
                return;
            } else {
                setError("Failed to generate quiz after multiple attempts. Please try again later.");
                setQuizState("ready");
            }
        }
    }, [moduleId, pollForQuiz, retryCount]);

    const checkQuizGenerationStatus = useCallback(async (isRetry = false) => {
        if (!isRetry) {
            setQuizState("checking_status");
            setError(null);
            setRetryCount(0);
        }

        try {
            const existingQuiz = await api.getQuizForModule(moduleId);

            // Extract the actual quiz object
            const quizData = (existingQuiz as any)?.quiz || existingQuiz;

            // Validate quiz data structure before setting it
            if (quizData &&
                typeof quizData === 'object' &&
                quizData.questions &&
                Array.isArray(quizData.questions) &&
                quizData.questions.length > 0) {

                setQuiz(quizData);
                setQuizState("ready");
            } else {
                await generateQuiz();
            }
        } catch (error) {
            try {
                await generateQuiz();
            } catch (genError) {
                setError("Unable to load or generate quiz. Please try again later.");
                setQuizState("ready");
            }
        }
    }, [moduleId, generateQuiz]);

    useEffect(() => {
        checkQuizGenerationStatus();
    }, [moduleId, checkQuizGenerationStatus]);

    useEffect(() => {
        if (quizState === 'taking' && learningPathId && moduleId && attempt && quiz) {
            setQuizAttemptContext(learningPathId, moduleId, quiz.id, attempt.id);
        }
    }, [quizState, learningPathId, moduleId, attempt, quiz, setQuizAttemptContext]);


    const handleSubmitQuiz = useCallback(async () => {
        if (!attempt || !quiz) return;
        try {
            setQuizState("submitting");
            const submission = {
                attempt_id: attempt.id,
                answers: Object.entries(answers).map(([qid, a]) => ({
                    question_id: parseInt(qid),
                    answer_text: a
                }))
            };
            const quizResults = await api.submitQuizAttempt(quiz.id, userId, submission);
            setResults(quizResults);
            setQuizState("results");
            if (learningPathId && moduleId) {
                setQuizAttemptContext(learningPathId, moduleId, undefined as any, undefined as any);
                setQuizContext(learningPathId, moduleId, undefined as any);
            }
            onQuizComplete?.();
        } catch (error) {
            setError("Failed to submit quiz. Please try again.");
            setQuizState("taking");
            if (learningPathId && moduleId) {
                setQuizAttemptContext(learningPathId, moduleId, undefined as any, undefined as any);
            }
        }
    }, [attempt, quiz, answers, userId, learningPathId, moduleId, onQuizComplete, setQuizAttemptContext, setQuizContext]);


    useEffect(() => {
        if (quizState === "taking" && timeRemaining !== null && timeRemaining > 0) {
            const timer = setTimeout(() => {
                setTimeRemaining(prev => prev !== null ? prev - 1 : null);
            }, 1000);
            return () => clearTimeout(timer);
        } else if (timeRemaining === 0) {
            handleSubmitQuiz();
        }
    }, [timeRemaining, quizState, handleSubmitQuiz]);

    useEffect(() => {
        if (quizState !== "taking" && attempt && learningPathId && moduleId) {
            setQuizAttemptContext(learningPathId, moduleId, undefined as any, undefined as any);
        }
    }, [quizState, attempt, learningPathId, moduleId, setQuizAttemptContext]);


    const safeClose = () => {
        if (learningPathId && moduleId) {
            setQuizAttemptContext(learningPathId, moduleId, undefined as any, undefined as any);
            setQuizContext(learningPathId, moduleId, undefined as any);
        }
        onClose();
    };

    const startQuiz = async () => {
        if (!quiz) return;
        try {
            setQuizState("loading");
            const newAttempt = await api.startQuizAttempt(quiz.id, userId);
            setAttempt(newAttempt);
            setQuizState("taking");

            const timeLimit = (quiz.estimated_completion_time || 10) * 60;
            setTimeRemaining(timeLimit);
            setCurrentQuestionIndex(0);
            setAnswers({});

            if (learningPathId && moduleId) {
                setQuizContext(learningPathId, moduleId, quiz.id);
                setQuizAttemptContext(learningPathId, moduleId, quiz.id, newAttempt.id);
            }
        } catch (error) {
            setError("Failed to start quiz. Please try again.");
            setQuizState("ready");
        }
    };

    const handleAnswerChange = (questionId: number, answer: string) => setAnswers(prev => ({
        ...prev,
        [questionId]: answer
    }));
    const handleNextQuestion = () => setCurrentQuestionIndex(prev => Math.min(prev + 1, (quiz?.questions.length || 1) - 1));
    const handlePreviousQuestion = () => setCurrentQuestionIndex(prev => Math.max(prev - 1, 0));
    const handleRetakeQuiz = () => {
        if (learningPathId && moduleId) {
            setQuizAttemptContext(learningPathId, moduleId, undefined as any, undefined as any);
            setQuizContext(learningPathId, moduleId, undefined as any);
        }
        setQuizState("ready");
        setAttempt(null);
        setResults(null);
        setAnswers({});
        setCurrentQuestionIndex(0);
        setTimeRemaining(null);
    };

    const formatTime = (seconds: number) => `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;

    const currentQuestion = quiz?.questions[currentQuestionIndex];

    if (quizState === "checking_status" || quizState === "loading") {
        return (
            <div className="flex items-center justify-center p-8 min-h-[300px]">
                <motion.div
                    className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full"
                    animate={{rotate: 360}}
                    transition={{duration: 1, repeat: Infinity, ease: "linear"}}
                />
                <span className="ml-3 text-neutral-dark">
            {quizState === "checking_status" ? "Checking quiz availability..." : "Loading..."}
        </span>
            </div>
        );
    }

    if (quizState === "generating") {
        return (
            <div className="p-6 min-h-[400px]">
                <GeneratingQuizLoader/>
            </div>
        );
    }

    if (quizState === "submitting") {
        return (
            <div className="p-6 min-h-[300px] flex items-center justify-center">
                <SubmittingQuizLoader/>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 text-center">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 inline-flex items-center">
                    <XCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0"/>
                    <span className="text-red-700">{error}</span>
                </div>
                <div className="flex gap-3 justify-center">
                    <Button onClick={() => checkQuizGenerationStatus()} variant="primary">
                        <RotateCcw className="w-4 h-4 mr-1"/>
                        Retry
                    </Button>
                    <Button onClick={safeClose} variant="hollow">Close</Button>
                </div>
            </div>
        );
    }

    if (quizUnavailable) {
        return (
            <div className="p-6 text-center text-neutral-secondary-light">
                <h2 className="text-xl font-bold mb-2">No Quiz Available</h2>
                <p>A quiz has not been generated for this module yet. Please check back later or contact your
                    instructor.</p>
            </div>
        );
    }

    if (quizState === "ready") {
        return (
            <div className="p-6">
                <div className="text-center mb-6">
                    <Brain className="w-12 h-12 text-primary mx-auto mb-4" strokeWidth={2.5}/>
                    <h2 className="text-2xl font-bold text-neutral-dark mb-2">Take Quiz: Test Your Knowledge</h2>
                    <p className="text-neutral-dark mb-4">
                        Take a quiz to reinforce what you've learned in this module and track your progress.
                    </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center">
                            <Clock className="w-5 h-5 text-blue-800 mr-2"/>
                            <span className="black font-medium">
                Estimated Time: {quiz?.estimated_completion_time || 10} minutes
              </span>
                        </div>
                        <div className="flex items-center">
                            <Award className="w-5 h-5 text-blue-800 mr-2"/>
                            <span className="black font-medium">{quiz?.total_questions} Questions</span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-3 justify-center">
                    <Button onClick={startQuiz} variant="primary" className="px-5">
                        <Play className="w-4 h-4 mr-1" strokeWidth={2.5}/>
                        Start Quiz
                    </Button>
                </div>
            </div>
        );
    }

    if (quizState === "taking" && quiz && currentQuestion) {
        return (
            <div className="p-6">
                {/* Header with progress and timer */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center">
            <span className="text-sm font-medium text-neutral-dark">
              Question {currentQuestionIndex + 1} of {quiz.questions.length}
            </span>
                        <div className="ml-4 w-32 bg-gray-200 rounded-full h-2">
                            <motion.div
                                className="bg-primary h-2 rounded-full"
                                initial={{width: 0}}
                                animate={{width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%`}}
                                transition={{duration: 0.3}}
                            />
                        </div>
                    </div>
                    {timeRemaining !== null && (
                        <div className="flex items-center text-sm font-medium">
                            <Clock className="w-4 h-4 mr-1"/>
                            <span className={timeRemaining < 300 ? "text-red-600" : "text-neutral-dark"}>
                {formatTime(timeRemaining)}
              </span>
                        </div>
                    )}
                </div>

                {/* Question */}
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-neutral-dark mb-4">
                        {currentQuestion.question_text}
                    </h3>

                    {/* Answer options based on question type */}
                    {currentQuestion.question_type === "multiple_choice" && currentQuestion.options && (
                        <div className="space-y-3">
                            {currentQuestion.options.map((option, index) => {
                                const optionText = getOptionText(option);
                                const optionValue = getOptionValue(option);
                                return (
                                    <label
                                        key={index}
                                        className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                                            answers[currentQuestion.id] === optionValue
                                                ? "border-primary bg-primary-light"
                                                : "border-gray-200 hover:border-primary/50"
                                        }`}
                                    >
                                        <input
                                            type="radio"
                                            name={`question-${currentQuestion.id}`}
                                            value={optionValue}
                                            checked={answers[currentQuestion.id] === optionValue}
                                            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                                            className="sr-only"
                                        />
                                        <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                                            answers[currentQuestion.id] === optionValue
                                                ? "border-primary bg-primary"
                                                : "border-gray-300"
                                        }`}>
                                            {answers[currentQuestion.id] === optionValue && (
                                                <div className="w-2 h-2 bg-white rounded-full m-0.5"/>
                                            )}
                                        </div>
                                        <span className="text-neutral-dark">{optionText}</span>
                                    </label>
                                );
                            })}
                        </div>
                    )}

                    {currentQuestion.question_type === "true_false" && (
                        <div className="space-y-3">
                            {["true", "false"].map((option) => (
                                <label
                                    key={option}
                                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                                        answers[currentQuestion.id] === option
                                            ? "border-primary bg-primary-light"
                                            : "border-gray-200 hover:border-primary/50"
                                    }`}
                                >
                                    <input
                                        type="radio"
                                        name={`question-${currentQuestion.id}`}
                                        value={option}
                                        checked={answers[currentQuestion.id] === option}
                                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                                        className="sr-only"
                                    />
                                    <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                                        answers[currentQuestion.id] === option
                                            ? "border-primary bg-primary"
                                            : "border-gray-300"
                                    }`}>
                                        {answers[currentQuestion.id] === option && (
                                            <div className="w-2 h-2 bg-white rounded-full m-0.5"/>
                                        )}
                                    </div>
                                    <span className="text-neutral-dark capitalize">{option}</span>
                                </label>
                            ))}
                        </div>
                    )}

                    {currentQuestion.question_type === "short_answer" && (
                        <textarea
                            value={answers[currentQuestion.id] || ""}
                            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                            placeholder="Type your answer here..."
                            className="w-full p-3 border border-gray-200 rounded-lg focus:border-primary focus:ring-1 focus:ring-primary resize-none"
                            rows={4}
                        />
                    )}
                </div>

                {/* Navigation */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <Button
                        onClick={handlePreviousQuestion}
                        variant="hollow"
                        disabled={currentQuestionIndex === 0}
                    >
                        <ArrowLeft className="w-4 h-4 mr-1" strokeWidth={2.5}/>
                        Previous
                    </Button>

                    <div className="flex gap-2">
                        {currentQuestionIndex < quiz.questions.length - 1 ? (
                            <Button
                                onClick={handleNextQuestion}
                                variant="primary"
                                disabled={!answers[currentQuestion.id] || answers[currentQuestion.id].trim() === ""}
                            >
                                Next
                                <ArrowRight className="w-4 h-4 ml-1" strokeWidth={2.5}/>
                            </Button>
                        ) : (
                            <Button
                                onClick={handleSubmitQuiz}
                                variant="success"
                                disabled={
                                    // Check if all questions are answered
                                    quiz.questions.some(q => !answers[q.id] || answers[q.id].trim() === "")
                                }
                            >
                                Submit Quiz
                                <CheckCircle className="w-4 h-4 ml-1" strokeWidth={2.5}/>
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    if (quizState === "results" && results) {
        const scorePercentage = Math.round(results.score); // Use score directly since it's already a percentage
        const passed = results.passed;

        return (
            <div className="p-8">
                <div className="text-center mb-6">
                    {passed ? (
                        <motion.div
                            initial={{scale: 0}}
                            animate={{scale: 1}}
                            transition={{type: "spring", stiffness: 200}}
                        >
                            <CheckCircle className="w-16 h-16 text-success mx-auto mb-4"/>
                        </motion.div>
                    ) : (
                        <motion.div
                            initial={{scale: 0}}
                            animate={{scale: 1}}
                            transition={{type: "spring", stiffness: 200}}
                        >
                            <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4"/>
                        </motion.div>
                    )}

                    <h2 className="text-2xl font-bold text-neutral-dark mb-4">
                        {passed ? "Congratulations!" : "Keep Learning!"}
                    </h2>

                    <div className="bg-gray-50 rounded-lg p-6 mb-4">
                        <div className="text-3xl font-bold text-primary mb-1">
                            {scorePercentage}%
                        </div>
                        <div className="text-sm text-neutral-dark mb-2">
                            {results.earned_points} out of {results.total_points} points
                        </div>
                        {results.time_taken && (
                            <div className="flex items-center justify-center text-sm text-neutral-dark">
                                <Clock className="w-4 h-4 mr-1"/>
                                Time taken: {formatTime(results.time_taken)}
                            </div>
                        )}
                        {results.skill_points_awarded > 0 && (
                            <div className="flex items-center justify-center text-sm text-green-600 font-medium mt-2">
                                <Award className="w-4 h-4 mr-1"/>
                                +{results.skill_points_awarded} Skill Points Awarded!
                            </div>
                        )}
                    </div>

                </div>


                <div className="flex gap-3 justify-center">
                    <Button onClick={handleRetakeQuiz} variant="primary">
                        <RotateCcw className="w-4 h-4 mr-1" strokeWidth={2.5}/>
                        Retake Quiz
                    </Button>
                </div>
            </div>
        );
    }

    return null;
}