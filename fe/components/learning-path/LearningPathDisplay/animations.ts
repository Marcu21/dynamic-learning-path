import type { Variants, Transition } from "framer-motion";

export const springTrans: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 24,
};

export const listVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: springTrans },
};

export const hoverEffect = { scale: 1.02, boxShadow: "0 8px 20px rgba(0,0,0,0.05)" };
