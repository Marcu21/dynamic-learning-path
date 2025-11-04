import { HTMLMotionProps } from "framer-motion";
import { ReactNode } from "react";

export type ButtonProps =
  Omit<HTMLMotionProps<"button">, "transition"> & {
    variant?:
      | "primary"
      | "secondary"
      | "alert"
      | "success"
      | "warning"
      | "hollow"
      | "accent";
    children: ReactNode;
    disabled?: boolean;
  };
