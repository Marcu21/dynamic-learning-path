export interface Quiz {
    id: number;
    module_id: number;
    title: string;
    description: string;
    passing_score: number;
    total_questions: number;
    is_active: boolean;
    created_at: string;
    questions: QuizQuestion[];
}

export interface QuizQuestion {
    id: number;
    quiz_id: number;
    question_text: string;
    question_type: "multiple_choice" | "true_false" | "short_answer";
    options?: string[];
    correct_answer?: string;
    explanation?: string;
    points: number;
    order_index: number;
}

export interface QuizForTaking {
    id: number;
    module_id: number;
    title: string;
    description: string;
    passing_score: number;
    total_questions: number;
    estimated_completion_time: number;
    questions: QuizQuestionForTaking[];
}

export interface QuizQuestionForTaking {
    id: number;
    question_text: string;
    question_type: "multiple_choice" | "true_false" | "short_answer";
    options?: string[];
    points: number;
    order_index: number;
}

export interface QuizAttempt {
    id: number;
    quiz_id: number;
    user_id: string;
    started_at: string;
    completed_at?: string;
    time_taken?: number;
    total_points: number;
    earned_points: number;
    score: number;
    passed: boolean;
    status: "in_progress" | "completed";
    skill_points_awarded: boolean;
    answers?: QuizAnswerResult[];  // Add answers field for detailed attempt data
}

export interface QuizSubmission {
    answers: QuizAnswer[];
}

export interface QuizAnswer {
    question_id: number;
    answer_text: string;
}

export interface QuizResult {
    attempt_id: number;
    quiz_id: number;
    user_id: string;
    score: number;
    total_points: number;
    earned_points: number;
    passed: boolean;
    skill_points_awarded: number;
    feedback: string;
    completed_at: string;
    time_taken: number;
    answers: QuizAnswerResult[];
}

export interface QuizAnswerResult {
    question_id: number;
    question_text: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    points_earned: number;
    ai_feedback: string;
    explanation?: string;
}

export interface QuizGenerationRequest {
    module_id: number;
    num_questions: number;
}

export interface QuizGenerationRequest {
    module_id: number;
    num_questions: number;
}

export interface QuizGenerationResponse {
    message: string;
    learning_path_title: string;
    total_modules: number;
    modules_needing_quizzes: number;
    status: "background_task_scheduled" | "no_action_needed";
}
