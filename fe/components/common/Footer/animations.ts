import type { Variants, Transition } from "framer-motion";

export const spring: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 25,
  mass: 0.8,
};

export const footerVariants: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.8,
      delayChildren: 0.1,
    },
  },
};

export const itemVariants: Variants = {
  hidden: { y: 30, opacity: 0, scale: 0.8 },
  visible: { y: 0, opacity: 1, scale: 1, transition: spring },
};

export const linkVariants: Variants = {
  initial: { scale: 1, y: 0 },
  hover: {
    scale: 1.00,
    y: -1,
    transition: { type: "spring", stiffness: 400, damping: 10 },
  },
  tap: { scale: 0.95 },
};