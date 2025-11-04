import {LucideProps} from "lucide-react";
import {ReactNode} from "react";

export interface GenerationDetailsCardProps {
  title: string;
  icon: React.ElementType<LucideProps>;
  children: ReactNode;
  defaultOpen?: boolean;
}