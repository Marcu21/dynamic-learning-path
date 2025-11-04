export interface QuizInterfaceProps {
  moduleId: number;
  userId: string;
  learningPathId?: number;
  onClose: () => void;
  onQuizComplete?: () => void;
}

export type QuizState = "loading" | "checking_status" | "generating" | "ready" | "taking" | "submitting" | "results";