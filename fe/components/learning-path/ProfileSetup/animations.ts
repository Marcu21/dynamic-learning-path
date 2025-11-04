import { type Variants } from "framer-motion";

export const spring = {
  type: "spring" as const,
  stiffness: 400,
  damping: 25,
  mass: 0.8,
};

export const containerVariants: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.8,
    y: 50,
    filter: "blur(10px)",
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    filter: "blur(0px)",
    transition: {
      ...spring,
      duration: 0.8,
      staggerChildren: 0.1,
    },
  },
};

export const itemVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 30,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: spring,
  },
};

export const stepVariants: Variants = {
  hidden: {
    opacity: 0,
    x: 50,
    scale: 0.95,
    filter: "blur(5px)",
  },
  visible: {
    opacity: 1,
    x: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: {
      ...spring,
      duration: 0.6,
    },
  },
  exit: {
    opacity: 0,
    x: -50,
    scale: 0.95,
    filter: "blur(5px)",
    transition: {
      duration: 0.4,
    },
  },
};