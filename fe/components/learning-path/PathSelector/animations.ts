import type { Variants, Transition } from "framer-motion";

export const buttonHover = { scale: 1.02 };
export const buttonTap = { scale: 0.98 };

export const toggleIcon: Transition = { duration: 0.2 };

export const dropdown: Variants = {
  hidden: { opacity: 0, y: -10, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.2 } },
};

export const itemHover = { x: 4 };
export const itemTap: Transition = { duration: 0.2 };
