export interface HeaderProps {
  username: string;
  onOpenSidebar?: () => void;
}

export type Particle = { left: number; top: number };

export interface NotificationPanelProps {
  onClose: () => void;
}