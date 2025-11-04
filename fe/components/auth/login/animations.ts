"use client"

import type { Variants, Transition } from "framer-motion"

export const spring: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
}

export const fadeSlide: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: spring },
}

export const floatAnimation: Variants = {
  animate: {
    y: [0, -10, 0],
    transition: { duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" },
  },
}

// New animations for enhanced error handling
export const messageSlide: Variants = {
  hidden: {
    opacity: 0,
    y: -20,
    scale: 0.95,
    filter: "blur(4px)",
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25,
      staggerChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.95,
    filter: "blur(4px)",
    transition: {
      duration: 0.2,
      ease: "easeInOut",
    },
  },
}

export const iconBounce: Variants = {
  hidden: { scale: 0, rotate: -180 },
  visible: {
    scale: 1,
    rotate: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20,
      delay: 0.1,
    },
  },
}

export const progressBar: Variants = {
  initial: { width: "100%" },
  animate: {
    width: "0%",
    transition: {
      duration: 5,
      ease: "linear",
    },
  },
}
