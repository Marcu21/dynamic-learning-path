"use client";

import React, {useState, useEffect, useMemo} from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { Clock, BookOpen, Plus, Calendar, Type, ArrowRight, Trophy, Play, Sparkles, Zap, Target, TrendingUp, MoreHorizontal, Trash2, Loader, ChevronLeft, ChevronRight as ChevronRightIcon, WandSparkles, Lightbulb, Rocket, Dna, Atom } from "lucide-react";
import { Button } from "@/components/common/Button";
import { api } from "@/lib/api";
import { styles, getCategoryButtonClasses } from "@/components/dashboard/PersonalDashboard/styles";
import * as anim from "@/components/dashboard/PersonalDashboard/animations";
import type { LearningPathFE, Category } from "@/components/dashboard/PersonalDashboard/types";
import { useChatLocationUpdater } from '@/context/ChatContext';
import BackgroundBlobs from "@/components/background/BackgroundBlobs";
import { usePagination, DOTS } from '@/hooks/usePagination';
import SortCombobox, { type SortOption, type SortOrder } from '@/components/dashboard/PersonalDashboard/SortCombobox';
import { LearningPathDashboardProps, PathCardProps } from "@/components/dashboard/PersonalDashboard/types";


const generatingMessages = [
  "Mapping out key concepts...",
  "Finding optimal learning resources...",
  "Creating personalized modules...",
  "Structuring your learning journey...",
];

const floatingIcons = [Lightbulb, Rocket, Dna, Atom];

const PATHS_PER_PAGE = 6;

const GeneratingCard = () => {
  const [currentMessage, setCurrentMessage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessage((prev) => (prev + 1) % generatingMessages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
      <motion.div
        className={styles.pathCard}
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: -20 }}
        transition={{ duration: 0.5 }}
        style={{ pointerEvents: "none" }}
      >
        <div className="flex flex-col justify-between h-full">
          <div className={`${styles.pathCardHeader} flex flex-col flex-grow`}>
            <div className="relative flex items-start justify-between mb-6">
              <div className="flex-1">
                <motion.h3
                  className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent mb-2"
                >
                  <div className="flex items-center">
                    <motion.div
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                    >
                      <WandSparkles className="w-6 h-6 mr-3 text-primary" />
                    </motion.div>
                    <span>Generating your path...</span>
                  </div>
                </motion.h3>
                <div className="text-neutral-secondary-light text-md relative h-6 overflow-hidden">
                  <AnimatePresence>
                    <motion.p
                      key={currentMessage}
                      className="absolute inset-0 flex items-center"
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{
                        duration: 0.25,
                        ease: [0.25, 0.46, 0.45, 0.94]
                      }}
                    >
                      {generatingMessages[currentMessage]}
                    </motion.p>
                  </AnimatePresence>
                </div>
              </div>
              <div className="relative ml-4">
                <AnimatePresence>
                  {floatingIcons.map((Icon, index) => (
                    <motion.div
                      key={index}
                      className="absolute top-0 right-0"
                      initial={{ opacity: 0, scale: 0, rotate: -180 }}
                      animate={{ opacity: currentMessage === index ? 1 : 0, scale: currentMessage === index ? 1 : 0, rotate: currentMessage === index ? 0 : 180 }}
                      transition={{ duration: 0.5 }}
                    >
                      <motion.div
                        className="w-12 h-12 bg-gradient-to-r from-primary to-accent rounded-xl flex items-center justify-center shadow-lg"
                        animate={{ y: [0, -8, 0], rotate: [0, 5, -5, 0] }}
                        transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                      >
                        <Icon className="w-6 h-6 text-white" />
                      </motion.div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
            <div className="mb-4 pt-4">
              <div className="w-full bg-neutral-accent-light/50 rounded-full h-2.5 relative overflow-hidden">
                <motion.div
                  className="absolute inset-0 h-full bg-gradient-to-r from-primary to-accent"
                  initial={{ x: "-100%" }}
                  animate={{ x: "100%" }}
                  transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                />
              </div>
            </div>
            <div className="flex items-center justify-between text-md text-neutral-secondary-light">
              <div className="flex items-center space-x-2">
                <motion.div
                  transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                >
                  <Clock className="w-4 h-4" />
                </motion.div>
                <span>Path will be ready soon...</span>
              </div>
              <motion.div
                className="flex items-center space-x-1"
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
              >
                <Sparkles className="w-4 h-4 text-accent" />
                <span className="text-primary font-semibold">AI at work</span>
              </motion.div>
            </div>
          </div>
          <div className={`${styles.pathCardFooter} mt-auto`}>
            <div className="flex items-center justify-center space-x-2">
              <span className="text-md font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Crafting something special...
              </span>
            </div>
          </div>
        </div>
      </motion.div>
  );
};

const PathCard = React.memo(({ path, index, openMenuId, toggleMenu, handleDeletePath }: PathCardProps) => {
  return (
    <Link href={`/paths/${path.id}`} passHref>
      <motion.div
        className={styles.pathCard}
        variants={anim.fadeSlide}
        whileHover={{ scale: 1.03 }}
        transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      >
        <div className="flex flex-col h-full">
          <div className={`${styles.pathCardHeader} flex-grow`}>
            <div className="absolute top-2.5 right-2.5 z-20" data-menu-container>
              <button
                onClick={(e) => toggleMenu(path.id, e)}
                className="p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <MoreHorizontal className="w-4 h-4 text-neutral-secondary-light hover:text-neutral-dark" />
              </button>
              <AnimatePresence>
                {openMenuId === path.id && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: -10 }}
                    className="absolute right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[120px] z-30"
                  >
                    <button
                      onClick={(e) => handleDeletePath(path, e)}
                      className="w-full px-3 py-2 text-left text-md text-red-600 hover:bg-red-50 transition-colors flex items-center space-x-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Delete</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <div className="flex items-start justify-between mb-3 pr-8">
              <div className="flex-1 min-w-0">
                <h3 className={styles.pathCardTitle}>{path.title}</h3>
                <p className={styles.pathCardDescription}>{path.description}</p>
              </div>
              {path.completion_percentage === 100 && (
                <div className="bg-success-light p-2 rounded-lg ml-3">
                  <Trophy className="w-5 h-5 text-success" />
                </div>
              )}
            </div>
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-md font-sans font-bold text-neutral-secondary-light">Progress</span>
                <span className="text-md font-sans font-semibold text-neutral-dark">{Math.round(path.completion_percentage)}%</span>
              </div>
              <div className="w-full bg-neutral-accent-light rounded-full h-2 relative overflow-hidden">
                <motion.div className="bg-gradient-to-r from-primary to-accent h-2 rounded-full relative" initial={{ width: 0 }} animate={{ width: `${path.completion_percentage}%` }} transition={{ duration: 1, delay: index * 0.1 }}>
                   <motion.div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent" {...anim.shimmerAnimation(index * 0.2)} />
                </motion.div>
              </div>
            </div>
            <div className="flex items-center justify-between text-md font-sans text-neutral-secondary-light">
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{path.estimated_days} days</span>
              </div>
            </div>
          </div>
          <div className={styles.pathCardFooter}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {/* Badge */}
                {path.completion_percentage === 100 && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{
                      backgroundColor: "#d4edda",
                      border: "1px solid #97d3a4",
                      color: "#000"
                    }}
                  >
                    Completed
                  </span>
                )}
                {path.completion_percentage === 0 && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{
                      backgroundColor: "#d6e4f5",
                      border: "1px solid #8daed8",
                      color: "#000"
                    }}
                  >
                    Ready to start
                  </span>
                )}
                {path.completion_percentage > 0 && path.completion_percentage < 100 && (
                  <span
                    className="px-2 py-0.5 text-xs rounded-full"
                    style={{
                      backgroundColor: "#fff3cd",
                      border: "1px solid #d6c385",
                      color: "#000"
                    }}
                  >
                    In progress
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-1 text-primary group-hover:translate-x-1 transition-transform">
                <span className="text-md font-sans font-bold">
                  {path.completion_percentage === 0
                    ? "Start"
                    : path.completion_percentage === 100
                    ? "View Path"
                    : "Continue"}
                </span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>


        </div>
      </motion.div>
    </Link>
  );
});

PathCard.displayName = 'PathCard';

export default function LearningPathDashboard({
  onSelectPath,
  onCreateNewPath,
  userProfile,
  userId,
  refreshKey,
  isGenerating,
  currentStatus,
  generatedPathId
}: LearningPathDashboardProps) {
  const { setDashboardContext } = useChatLocationUpdater();
  const [paths, setPaths] = useState<LearningPathFE[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [pathToDelete, setPathToDelete] = useState<LearningPathFE | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedSort, setSelectedSort] = useState<string>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortOptions: SortOption[] = [
    {
      id: 'name',
      label: 'Name',
      icon: Type,
      getValue: (path: LearningPathFE) => path.title.toLowerCase()
    },
    {
      id: 'date',
      label: 'Date',
      icon: Calendar,
      getValue: (path: LearningPathFE) => {
        return path.id;
      }
    },
    {
      id: 'progress',
      label: 'Progress',
      icon: TrendingUp,
      getValue: (path: LearningPathFE) => path.completion_percentage
    }
  ];

  useEffect(() => {
    const fetchLearningPaths = async () => {
      if (userProfile && userProfile.name && userId) {
        try {
          setError(null);
          // Set loading to false immediately if we're fetching, to prevent extra loading screen
          setLoading(true);
          const realPaths = await api.getUserLearningPaths(userId);
          const convertedPaths: LearningPathFE[] = realPaths.map(path => ({
            id: path.id, user_id: path.user_id, title: path.title, description: path.description,
            estimated_days: path.estimated_days, completion_percentage: path.completion_percentage, created_at: path.created_at
          }));
          setPaths(convertedPaths);
        } catch (error) {
          setError("Failed to load learning paths. Please try again.");
          setPaths([]);
        } finally {
          setLoading(false);
        }
      } else {
        setPaths([]);
        setLoading(false);
      }
    };

    fetchLearningPaths();
  }, [userProfile, userId, refreshKey]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openMenuId) {
        const target = event.target as Element;
        if (!target.closest('[data-menu-container]')) setOpenMenuId(null);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [openMenuId]);

  useEffect(() => {
    setDashboardContext();
  }, [setDashboardContext]);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedCategory]);

  const handleDeletePath = async (path: LearningPathFE, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOpenMenuId(null);
    setPathToDelete(path);
    setShowDeleteConfirmation(true);
  };

  const confirmDeletePath = async () => {
    if (!pathToDelete || isDeleting) return;
    setIsDeleting(true);
    try {
      await api.deleteLearningPath(pathToDelete.id);
      const updatedPaths = paths.filter(p => p.id !== pathToDelete.id);
      setPaths(updatedPaths);
      setShowDeleteConfirmation(false);
      setPathToDelete(null);
    } catch (error) {
      alert("Failed to delete learning path. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  const toggleMenu = (pathId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOpenMenuId(openMenuId === pathId ? null : pathId);
  };

  const categories: Category[] = [
    { id: "all", label: "All Paths", icon: BookOpen },
    { id: "in-progress", label: "In Progress", icon: Play },
    { id: "completed", label: "Completed", icon: Trophy },
  ];

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const sortPaths = (paths: LearningPathFE[]) => {
    const selectedOption = sortOptions.find(opt => opt.id === selectedSort);
    if (!selectedOption) return paths;

    return [...paths].sort((a, b) => {
      const aValue = selectedOption.getValue(a);
      const bValue = selectedOption.getValue(b);

      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });
  };

  const handleSortChange = (sortId: string, order: SortOrder) => {
    setSelectedSort(sortId);
    setSortOrder(order);
  };

  const filteredPaths = useMemo(() => {
    let filtered = paths;

    // Apply category filter
    if (selectedCategory !== "all") {
      filtered = filtered.filter(path => {
        if (selectedCategory === "completed") return path.completion_percentage === 100;
        if (selectedCategory === "in-progress") return path.completion_percentage > 0 && path.completion_percentage < 100;
        if (selectedCategory === "not-started") return path.completion_percentage === 0;
        return true;
      });
    }

    // Apply sorting
    return sortPaths(filtered);
  }, [paths, selectedCategory, sortPaths]);

  const totalPages = Math.ceil(filteredPaths.length / PATHS_PER_PAGE);
  const startIndex = (currentPage - 1) * PATHS_PER_PAGE;

  useEffect(() => {
    // After deletion, if current page is beyond total pages, go to previous page
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  const paginationRange = usePagination({
    currentPage,
    totalPages,
  });

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const totalPaths = paths.length;
  const completedPaths = paths.filter((p) => p.completion_percentage === 100).length;
  const inProgressPaths = paths.filter((p) => p.completion_percentage > 0 && p.completion_percentage < 100).length;

  // Determine if we should show the loading card
  const shouldShowLoadingCard = isGenerating && currentStatus !== 'COMPLETED';

  const capacityThisPage = PATHS_PER_PAGE - (shouldShowLoadingCard ? 1 : 0);
  const paginatedPaths = filteredPaths.slice(startIndex, startIndex + capacityThisPage);

  return (
    <motion.div className={styles.pageContainer} initial="hidden" animate="visible" variants={anim.pageVariants}>

      <BackgroundBlobs />

      <div className={styles.mainContent}>

        <motion.div className={styles.statsGrid} variants={anim.fadeSlide}>
          <motion.div className={styles.statCard} whileHover={anim.statCardHover} transition={anim.spring}>
            <div className="flex items-center space-x-3">
              <motion.div className={`${styles.statCardIconWrapper} bg-gradient-to-r from-primary to-accent`}>
                <Target className="w-5 h-5 text-white" />
                <motion.div className="absolute inset-0 rounded-full bg-gradient-to-r from-primary to-accent" {...anim.statIconPulseAnimation(0)} />
              </motion.div>
              <div>
                <p className={styles.statCardValue}>{totalPaths}</p>
                <p className={styles.statCardLabel}>Total Paths</p>
              </div>
            </div>
          </motion.div>
          <motion.div className={styles.statCard} whileHover={anim.statCardHover} transition={anim.spring}>
             <div className="flex items-center space-x-3">
              <motion.div className={`${styles.statCardIconWrapper} bg-gradient-to-r from-blue-500 to-cyan-500`}>
                <TrendingUp className="w-5 h-5 text-white" />
                <motion.div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500" {...anim.statIconPulseAnimation(0.5)} />
              </motion.div>
              <div>
                <p className={styles.statCardValue}>{inProgressPaths}</p>
                <p className={styles.statCardLabel}>In Progress</p>
              </div>
            </div>
          </motion.div>
          <motion.div className={styles.statCard} whileHover={anim.statCardHover} transition={anim.spring}>
            <div className="flex items-center space-x-3">
              <motion.div className={`${styles.statCardIconWrapper} bg-gradient-to-r from-green-500 to-emerald-500`}>
                <Trophy className="w-5 h-5 text-white" />
                <motion.div className="absolute inset-0 rounded-full bg-gradient-to-r from-green-500 to-emerald-500" {...anim.statIconPulseAnimation(1)} />
              </motion.div>
              <div>
                <p className={styles.statCardValue}>{completedPaths}</p>
                <p className={styles.statCardLabel}>Completed</p>
              </div>
            </div>
          </motion.div>
        </motion.div>

        <motion.div className={styles.filterContainer} variants={anim.fadeSlide}>
          <div className={styles.filterButtonsWrapper}>
            {categories.map((category) => (
              <motion.button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={getCategoryButtonClasses(selectedCategory === category.id)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <category.icon className="w-4 h-4" />
                <span>{category.label}</span>
              </motion.button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <SortCombobox
              selectedSort={selectedSort}
              sortOrder={sortOrder}
              onSortChange={handleSortChange}
              sortOptions={sortOptions}
            />
            <Link href="/paths/new" passHref>
              <Button
                disabled={isGenerating}
                className="flex items-center bg-gradient-to-r from-primary to-accent hover:from-primary hover:to-accent-dark relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed text-md py-2 px-4"
              >
                <Plus className="w-5 h-5" />
                <span className="font-bold">{isGenerating ? 'Generating...' : 'Create New Path'}</span>
                {!isGenerating && (
                  <motion.div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent" {...anim.shimmerAnimation(2)} />
                )}
              </Button>
            </Link>
          </div>
        </motion.div>

        {filteredPaths.length > 0 && (
          <motion.div className="mb-6 text-center" variants={anim.fadeSlide}>
            <motion.div className="text-neutral-secondary-light font-sans flex items-center justify-center space-x-2" animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 4, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}>
              <motion.div transition={{ duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}>
                <Sparkles className="w-4 h-4 text-accent" />
              </motion.div>
              <span>
                {inProgressPaths > 0 ? `Keep going! You have ${inProgressPaths} path${inProgressPaths > 1 ? "s" : ""} in progress` : completedPaths > 0 ? "Great job on your completed paths! Ready for a new challenge?" : "Your learning journey starts here. Choose a path to begin!"}
              </span>
              <motion.div transition={{ duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}>
                <Zap className="w-4 h-4 text-primary" />
              </motion.div>
            </motion.div>
          </motion.div>
        )}

        <motion.div className={styles.pathGrid} variants={{ visible: { transition: { staggerChildren: 0.1 } } }}>
          <AnimatePresence>
            {shouldShowLoadingCard && <GeneratingCard />}
          </AnimatePresence>
          {paginatedPaths.map((path, index) => (
            <PathCard
              key={path.id}
              path={path}
              index={index}
              openMenuId={openMenuId}
              toggleMenu={toggleMenu}
              handleDeletePath={handleDeletePath}
            />
          ))}
        </motion.div>

        {totalPages > 1 && (
    <motion.div
        className="flex items-center justify-center space-x-2 pt-8"
        variants={anim.fadeSlide}
    >
        {/* Back Button */}
        <motion.button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="w-10 h-10 flex items-center justify-center rounded-full bg-white/20 backdrop-blur-sm border border-white/30 text-neutral-dark hover:bg-white/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            whileHover={{ scale: currentPage === 1 ? 1 : 1.1 }}
            whileTap={{ scale: currentPage === 1 ? 1 : 0.9 }}
        >
            <ChevronLeft className="w-5 h-5" />
        </motion.button>

        {/* Page Number */}
        {paginationRange?.map((pageNumber, index) => {
            if (pageNumber === DOTS) {
                return <span key={`dots-${index}`} className="w-10 h-10 flex items-center justify-center text-neutral-secondary-light">&#8230;</span>;
            }

            const isActive = currentPage === pageNumber;
            return (
                <motion.button
                    key={pageNumber}
                    onClick={() => handlePageChange(pageNumber as number)}
                    className={`w-10 h-10 flex items-center justify-center rounded-full font-semibold transition-all duration-300
                        ${isActive 
                            ? 'bg-primary text-white shadow-lg' 
                            : 'bg-white/20 backdrop-blur-sm border border-white/30 text-neutral-dark hover:bg-white/40'
                        }`
                    }
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                >
                    {pageNumber}
                </motion.button>
            );
        })}

        {/* Forward button */}
        <motion.button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="w-10 h-10 flex items-center justify-center rounded-full bg-white/20 backdrop-blur-sm border border-white/30 text-neutral-dark hover:bg-white/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            whileHover={{ scale: currentPage === totalPages ? 1 : 1.1 }}
            whileTap={{ scale: currentPage === totalPages ? 1 : 0.9 }}
        >
            <ChevronRightIcon className="w-5 h-5" />
        </motion.button>
    </motion.div>
)}

        <AnimatePresence>
          {loading && (
            <motion.div className="text-center py-12" variants={anim.fadeSlide} key="loader">
              <Loader className="w-12 h-12 text-primary mx-auto animate-spin" />
              <p className="mt-4 text-neutral-secondary-light">Loading paths...</p>
            </motion.div>
          )}

          {error && !loading && (
            <motion.div className="text-center py-12" variants={anim.fadeSlide} key="error">
              <p className="text-red-500">{error}</p>
            </motion.div>
          )}

          {!isGenerating && filteredPaths.length === 0 && !loading && !error && (
            <motion.div className={styles.emptyStateContainer} variants={anim.fadeSlide} key="empty">
              <div className={styles.emptyStateCard}>
                {/* Context-aware icon */}
                {selectedCategory === "completed" ? (
                  <Trophy className="w-12 h-12 text-neutral-secondary-light mx-auto mb-4" />
                ) : selectedCategory === "in-progress" ? (
                  <Play className="w-12 h-12 text-neutral-secondary-light mx-auto mb-4" />
                ) : (
                  <BookOpen className="w-12 h-12 text-neutral-secondary-light mx-auto mb-4" />
                )}

                {/* Context-aware title */}
                <h3 className="text-xl font-display font-semibold text-neutral-dark mb-2">
                  {selectedCategory === "completed"
                    ? (totalPaths === 0 ? "No learning paths yet" : "No completed paths yet")
                    : selectedCategory === "in-progress"
                    ? (totalPaths === 0 ? "No learning paths yet" : "No paths in progress")
                    : "No learning paths yet"
                  }
                </h3>

                {/* Context-aware message */}
                <p className="text-neutral-secondary-light font-sans mb-4">
                  {selectedCategory === "completed"
                    ? (totalPaths === 0
                      ? "Create your first learning path to start your learning journey!"
                      : "Complete your first learning path to see it here. Keep going!")
                    : selectedCategory === "in-progress"
                    ? (totalPaths === 0
                      ? "Create your first learning path to start learning!"
                      : "Start a learning path to track your progress here.")
                    : "Create your first learning path to get started on your learning journey!"
                  }
                </p>

                {totalPaths === 0 || selectedCategory === "all" ? (
                  <Link href="/paths/new">
                    <Button variant="primary">Create Your First Path</Button>
                  </Link>
                ) : (
                  <Button variant="primary" onClick={() => setSelectedCategory('all')}>
                    {selectedCategory === "completed" ? "View All Paths" : "Browse All Paths"}
                  </Button>
                )}

                {/* Additional context for filtered sections */}
                {selectedCategory !== "all" && totalPaths > 0 && (
                  <p className="text-sm text-neutral-secondary-light mt-4 opacity-75">
                    You have {totalPaths} total learning path{totalPaths !== 1 ? 's' : ''} across all categories
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {showDeleteConfirmation && pathToDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => !isDeleting && setShowDeleteConfirmation(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl"
            >
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
                  <Trash2 className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Learning Path</h3>
                <p className="text-md text-gray-500 mb-4">Are you sure you want to permanently delete "{pathToDelete.title}"?</p>
                <div className="flex space-x-3">
                  <Button onClick={() => setShowDeleteConfirmation(false)} disabled={isDeleting} variant="hollow" className="flex-1">
                    Cancel
                  </Button>
                  <Button onClick={confirmDeletePath} disabled={isDeleting} className="flex-1 bg-red-600 hover:bg-red-700">
                    {isDeleting ? "Deleting..." : "Delete"}
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}