"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown, BookOpen, Clock, Star, ArrowRight, Search } from "lucide-react";
import type { PathSelectorProps } from "@/components/learning-path/PathSelector/types";
import * as styles from "@/components/learning-path/PathSelector/styles";
import * as anim from "@/components/learning-path/PathSelector/animations";

export default function PathSelector({
  paths,
  onSelectPath,
  currentPathId,
}: PathSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Filter out the current path and apply search filter
  const filtered = paths
    .filter((p) => p.id !== currentPathId) // Exclude current path
    .filter((p) =>
      p.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
  paths.find((p) => p.id === currentPathId);
  return (
    <div className={styles.wrapper}>
      {/* Trigger */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={styles.trigger}
        whileHover={anim.buttonHover}
        whileTap={anim.buttonTap}
      >
        <div className={styles.triggerContent}>
          <div className={styles.iconBg}>
            <BookOpen className="w-5 h-5 text-primary" />
          </div>
          <div className="flex flex-col items-start">
            <h3  className={`${styles.title} mb-0`}>
              Switch Learning Path
            </h3>
            {paths.filter(p => p.id !== currentPathId).length > 0 && (
              <p className={`${styles.subtitle} mt-0`}>
                Choose from {paths.filter(p => p.id !== currentPathId).length} other paths
              </p>
            )}
          </div>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={anim.toggleIcon}
        >
          <ChevronDown className="w-5 h-5 text-neutral-secondary-light" />
        </motion.div>
      </motion.button>

      {/* Dropdown */}
      {isOpen && (
        <motion.div
          className={styles.dropdown}
          initial="hidden"
          animate="visible"
          exit="hidden"
          variants={anim.dropdown}
        >
          {/* Search */}
          <div className={styles.searchWrapper}>
            <div className="relative">
              <Search className={styles.searchIcon} />
              <input
                type="text"
                placeholder="Search paths…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={styles.searchInput}
              />
            </div>
          </div>

          {/* List */}
          <div className={styles.list}>
            {filtered.length === 0 ? (
              <div className={styles.emptyState}>
                {searchTerm 
                  ? "No other paths found matching your search." 
                  : "No other learning paths available."}
              </div>
            ) : (
              filtered.map((path) => (
                <motion.button
                  key={path.id}
                  onClick={() => {
                    onSelectPath(path);
                    setIsOpen(false);
                  }}
                  className={`${styles.itemBase} ${styles.itemHover}`}
                  whileHover={anim.itemHover}
                  transition={anim.itemTap}
                >
                  <div className={styles.itemContent}>
                    <h4 className="font-display font-semibold text-neutral-dark mb-1">
                      {path.title}
                    </h4>
                    <p className="text-sm text-neutral-secondary-light font-sans mb-2 line-clamp-2">
                      {path.description}
                    </p>
                    <div className="flex items-center space-x-3 text-xs font-sans text-neutral-secondary-light">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{path.estimated_days} days</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3" />
                        <span>{Math.round(path.completion_percentage)}%</span>
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-neutral-secondary-light ml-3 mt-1" />
                </motion.button>
              ))
            )}
          </div>
        </motion.div>
      )}

      {/* Click-away */}
      {isOpen && <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />}
    </div>
  );
}