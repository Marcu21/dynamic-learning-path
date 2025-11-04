export interface Notification {
  id: string;
  message: string;
  date: Date;
  read: boolean;
  pathId?: number;
  teamId?: string;
}

