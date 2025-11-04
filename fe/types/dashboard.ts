export interface GenerationState {
  inProgress: boolean;
  teamId: string | null;
  currentStatus?: string;
  generatedPathId?: string | null;
}

export interface DashboardPageProps {
  generationState: GenerationState;
}