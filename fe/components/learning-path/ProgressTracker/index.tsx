"use client";

import { motion } from "framer-motion";
import { BarChart3, CheckCircle, ListTodo } from "lucide-react";
import type { Module } from "@/types/learning-paths";
import { containerVariants, barVariants, cardVariants } from "./animations";
import { defaultStyles, teamStyles } from "./styles";

export default function ProgressTracker({
  completedModules,
  totalModules,
  currentModule,
  isTeam = false,
}: {
  completedModules: Set<number>;
  totalModules: number;
  currentModule: Module | null;
  isTeam?: boolean;
}) {
  const s = isTeam ? teamStyles : defaultStyles;

  const rate =
    totalModules > 0
      ? Math.round((completedModules.size / totalModules) * 100)
      : 0;
  const remaining = totalModules - completedModules.size;

  return (
    <motion.div
      className={s.wrapper}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Heading */}
      <motion.h3 className={s.heading} variants={cardVariants}>
        <BarChart3 className={s.headingIcon} />
        <span className={s.headingText}>Progress Overview</span>
      </motion.h3>

      <div className={s.section}>
        {/* Overall Progress */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <motion.span className={s.overallLabel} variants={cardVariants}>
              Overall Progress
            </motion.span>
            <motion.span className={s.overallValue} variants={cardVariants}>
              {rate}%
            </motion.span>
          </div>
          <div className={s.barContainer}>
            <motion.div
              className={s.barFill}
              custom={rate}
              initial="hidden"
              animate="visible"
              variants={barVariants}
            />
          </div>
        </div>

        {/* Completed / Remaining */}
        <div className={s.gridSection}>
          <div className="hover:scale-105 transition-transform duration-200">
             <motion.div
            className="flex flex-col items-center justify-center p-4 rounded-lg bg-success-light transition-all" // Remove cursor-pointer
            variants={cardVariants}
          >
            <CheckCircle className={s.statIconCompleted} />
            <div className={s.statValue}>{completedModules.size}</div>
            <div className={s.statLabel}>Completed</div>
          </motion.div>

          </div>
         
         <div className="hover:scale-105 transition-transform duration-200">
          <motion.div
            className="flex flex-col items-center justify-center p-4 rounded-lg bg-primary-light transition-all" // Remove cursor-pointer
            variants={cardVariants}
          >
            <ListTodo className={s.statIconRemaining} />
            <div className={s.statValue}>{remaining}</div>
            <div className={s.statLabel}>Remaining</div>
          </motion.div>
         </div>

        </div>

      </div>
    </motion.div>
  );
}