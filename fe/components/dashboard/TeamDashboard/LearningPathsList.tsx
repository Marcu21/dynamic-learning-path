import {useState, useEffect, useRef, useMemo} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/router";
import { BookOpen, Play, Trophy, Plus, ArrowRight, Clock, Calendar, Type, TrendingUp, Sparkles, ChevronLeft, ChevronRight as ChevronRightIcon, Trash2, MoreHorizontal } from "lucide-react";
import { Button } from "@/components/common/Button";
import { LearningPathsListProps } from "./types";
import { teamStyles, categories } from "./styles";
import GeneratingPathCard from './GeneratingPathCard';
import { usePagination, DOTS } from '@/hooks/usePagination';
import SortCombobox, { type SortOption, type SortOrder } from '@/components/dashboard/PersonalDashboard/SortCombobox';

const CARDS_PER_PAGE = 6;

const sortOptions: SortOption[] = [
  {
    id: 'name',
    label: 'Name',
    icon: Type,
    getValue: (path: any) => path.title?.toLowerCase() || ''
  },
  {
    id: 'date',
    label: 'Date',
    icon: Calendar,
    getValue: (path: any) => {
      return path.created_at ? new Date(path.created_at).getTime() : 0;
    }
  },
  {
    id: 'progress',
    label: 'Progress',
    icon: TrendingUp,
    getValue: (path: any) => path.completion_percentage || 0
  }
];

export default function LearningPathsList({
  paths,
  selectedCategory,
  onSelectCategory,
  onSelectPath,
  onShowTeamProfileSetup,
  isTeamLead,
  isGenerating,
  onDeletePath,
}: LearningPathsListProps) {
  const router = useRouter();
  const [currentPage, setCurrentPage] = useState(1);
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [selectedSort, setSelectedSort] = useState<string>('date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const getIconComponent = (iconName: string) => {
    const icons = { BookOpen, Play, Trophy };
    return icons[iconName as keyof typeof icons] || BookOpen;
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openMenuId !== null && menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [openMenuId]);

  const toggleMenu = (e: React.MouseEvent, pathId: number) => {
    e.stopPropagation();
    setOpenMenuId(prev => (prev === pathId ? null : pathId));
  };

  const sortPaths = (paths: any[]) => {
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
  
  const filteredAndSortedPaths = useMemo(() => {
    let filtered = paths.filter((path) => {
      if (selectedCategory === "all") return true;
      if (selectedCategory === "completed") return path.completion_percentage === 100;
      if (selectedCategory === "in-progress") return path.completion_percentage > 0 && path.completion_percentage < 100;
      return true;
    });
    
    return sortPaths(filtered);
  }, [paths, selectedCategory, sortPaths]);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedCategory, selectedSort, sortOrder]);

  const startIndex = (currentPage - 1) * CARDS_PER_PAGE;
  const totalPages = Math.ceil(filteredAndSortedPaths.length / CARDS_PER_PAGE);
  const capacityThisPage = CARDS_PER_PAGE - (isGenerating ? 1 : 0);
  const paginatedPaths = filteredAndSortedPaths.slice(startIndex, startIndex + capacityThisPage);

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

  const handlePathClick = (path: any) => {
    if (onSelectPath) {
      onSelectPath(path);
    } else {
      router.push(`/paths/${path.id}?teamId=${router.query.teamId}`);
    }
  };

  const handleSortChange = (sortId: string, order: SortOrder) => {
    setSelectedSort(sortId);
    setSortOrder(order);
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap items-center justify-between gap-4"
      >
        <div className="flex flex-wrap gap-3">
          {categories.map((category) => {
            const isActive = selectedCategory === category.id;
            const Icon = getIconComponent(category.icon);
            return (
              <motion.button
                key={category.id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onSelectCategory(category.id)}
                className={`flex items-center px-4 py-2 rounded-lg font-bold font-inter text-md transition-all relative overflow-hidden gap-2 ${
                  isActive ? teamStyles.categoryActive : teamStyles.categoryInactive
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{category.label}</span>
              </motion.button>
            );
          })}
        </div>

        <SortCombobox
          selectedSort={selectedSort}
          sortOrder={sortOrder}
          onSortChange={handleSortChange}
          sortOptions={sortOptions}
        />
      </motion.div>

      <div className="space-y-6">
        {isTeamLead && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid gap-6"
          >
            <div
              className={`rounded-2xl p-8 text-center group transition-all duration-300 ${
                paths.length === 0 
                  ? "bg-gradient-to-br from-purple-150 to-[#E9E4F0] border-2 border-dashed border-[#5E35B1]/30 hover:border-[#5E35B1]/50" 
                  : "bg-gradient-to-br from-[#5E35B1]/10 to-[#8E44AD]/5 border-2 border-dashed border-[#5E35B1]/30 hover:border-[#5E35B1]/50"
              }`}
            >
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="flex flex-col items-center space-y-4"
              >
                <div className="p-4 rounded-2xl bg-gradient-to-br from-[#5E35B1] to-[#380A63] text-white shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                  <Plus className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[#380A63] mb-2">
                    {paths.length === 0 ? "Create Your Team's First Learning Path" : "Create a New Team Learning Path"}
                  </h3>
                  <p className="text-neutral-dark mb-4 max-w-lg">
                    {paths.length === 0 ? "Get started by designing a custom learning journey tailored to your team's goals." : "Design a new learning journey for your team's skill development."}
                  </p>
                  <Button
                    onClick={onShowTeamProfileSetup}
                    disabled={isGenerating}
                    className={`${teamStyles.primaryButton} disabled:opacity-60 disabled:cursor-not-allowed`}
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        <Sparkles className="w-4 h-4 mr-1" />
                        AI is working...
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4 mr-2" />
                        Create New Path
                      </>
                    )}
                  </Button>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
        {isGenerating && <GeneratingPathCard />}

        {paginatedPaths.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="grid gap-6"
          >
            {paginatedPaths.map((path, index) => (
              <motion.div
                key={path.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
                onClick={() => handlePathClick(path)}
                className={teamStyles.pathCard}
              >
                <div className="flex flex-col h-full">
                  <div className="flex items-start space-x-4">
                    <div className="p-3 mt-1 rounded-xl bg-gradient-to-br from-[#5E35B1]/20 to-[#8E44AD]/10 text-[#380A63] group-hover:from-[#5E35B1]/30 group-hover:to-[#8E44AD]/20 transition-all duration-300">
                      <BookOpen className="w-6 h-6" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-bold text-[#380A63] group-hover:text-[#5E35B1] transition-colors duration-300">
                        {path.title}
                      </h3>
                      <p className="text-neutral-secondary-light text-md mt-1 line-clamp-2">
                        {path.description || "Team learning path"}
                      </p>
                    </div>
                    {isTeamLead && (
                      <div ref={openMenuId === path.id ? menuRef : null} className="relative z-20">
                        <motion.button
                            onClick={(e) => toggleMenu(e, path.id)}
                            className="rounded-full hover:bg-purple-100/50"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                        >
                            <MoreHorizontal className="w-5 h-5 text-purple-700/90" />
                        </motion.button>
                        <AnimatePresence>
                          {openMenuId === path.id && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.9, y: -10 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.9, y: -10 }}
                              className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1"
                            >
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeletePath(path);
                                  setOpenMenuId(null);
                                }}
                                className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                                <span>Delete</span>
                              </button>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}
                  </div>

                  <div className="mt-auto pt-4 space-y-2">
                    <div className="flex items-center justify-between text-md text-neutral-dark">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>{path.estimated_days || 0} days</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Trophy className="w-4 h-4" />
                          <span>{Math.round(path.completion_percentage || 0)}% complete</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 text-purple-700 text-md font-semibold group-hover:translate-x-1 transition-transform">
                          <span>Continue</span>
                          <ArrowRight className="w-4 h-4" />
                      </div>
                    </div>
                    <div className="w-full h-2 bg-[#380A63]/10 rounded-full">
                      <div
                        className="h-full bg-gradient-to-r from-[#5E35B1] to-[#8E44AD] rounded-full transition-all duration-500"
                        style={{ width: `${Math.round(path.completion_percentage || 0)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          filteredAndSortedPaths.length === 0 && !isGenerating && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-center py-12"
            >
                <div className="p-4 rounded-2xl bg-gradient-to-br from-[#5E35B1]/10 to-[#8E44AD]/5 text-[#380A63]/60 w-fit mx-auto mb-4">
                    <BookOpen className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-[#380A63] mb-2">
                    No learning paths found
                </h3>
                <p className="text-[#380A63]/70 mb-6">
                    No paths found in the "{categories.find(c => c.id === selectedCategory)?.label}" category.
                </p>
            </motion.div>
          )
        )}

        {totalPages > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center justify-center space-x-2 pt-8"
          >
            <Button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 disabled:opacity-50"
              variant="hollow"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            {paginationRange?.map((pageNumber, index) => {
               if (pageNumber === DOTS) {
                return <span key={`dots-${index}`} className="px-4 py-2 text-neutral-secondary-light">&#8230;</span>;
              }

              return (
                <Button
                  key={pageNumber}
                  onClick={() => handlePageChange(pageNumber as number)}
                  className={`px-4 py-2 ${currentPage === pageNumber ? '' : 'bg-white'}`}
                  variant={currentPage === pageNumber ? 'primary' : 'hollow'}
                >
                  {pageNumber}
                </Button>
              );
            })}

            <Button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 disabled:opacity-50"
              variant="hollow"
            >
              <ChevronRightIcon className="w-4 h-4" />
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  );
}