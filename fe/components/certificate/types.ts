export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

export interface CertificateProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
  pathTitle: string;
  completionDate?: Date;
  totalModules: number;
  estimatedDays?: number;
}