import { type Transition, type Variants } from "framer-motion";

export const spring: Transition = { type: "spring", stiffness: 300, damping: 30 };

export const pageVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

export const fadeSlide: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: "spring" } },
};

export const cardHover: Variants = {
  hover: {
    scale: 1.02,
    y: -5,
    transition: { type: "spring", stiffness: 400, damping: 25 },
  },
};

export const statCardHover = {
  scale: 1.02,
  y: -2,
};

export const statIconPulseAnimation = (delay: number = 0) => ({
  animate: {
    scale: [1, 1.4, 1],
    opacity: [0.5, 0, 0.5],
  },
  transition: {
    duration: 2,
    repeat: Number.POSITIVE_INFINITY,
    ease: "easeInOut" as const,
    delay,
  },
});

export const shimmerAnimation = (delay: number = 0) => ({
  animate: { x: ["-100%", "100%"] },
  transition: {
    duration: 2,
    repeat: Number.POSITIVE_INFINITY,
    ease: "easeInOut" as const,
    delay,
  },
});

export const floatingElementAnimation = (
  duration: number,
  delay: number = 0
) => ({
  animate: {
    scale: [1, 1.2, 1],
    rotate: [0, 180, 360],
  },
  transition: {
    duration,
    repeat: Number.POSITIVE_INFINITY,
    ease: "easeInOut" as const,
    delay,
  },
});