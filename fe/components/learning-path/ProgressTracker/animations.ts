import type { Variants } from "framer-motion";

export const containerVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { when: "beforeChildren", staggerChildren: 0.2 },
  },
};

export const barVariants: Variants = {
  hidden: { width: 0 },
  visible: (rate: number) => ({
    width: `${rate}%`,
    transition: { type: "spring", stiffness: 100, damping: 20, duration: 1 },
  }),
};

export const cardVariants: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring", stiffness: 200, damping: 20 },
  },
};
