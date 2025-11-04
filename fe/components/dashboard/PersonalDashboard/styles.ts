export const styles = {
  pageContainer: "min-h-screen bg-neutral-accent",
  mainContent: "max-w-7xl mx-auto px-6 py-8 relative z-10",
  statsGrid: "grid grid-cols-1 md:grid-cols-3 gap-4 mb-8",
  statCard: "bg-neutral-accent rounded-xl p-4 border border-neutral-secondary-dark shadow-lg relative overflow-hidden",
  statCardIconWrapper: "w-10 h-10 rounded-full flex items-center justify-center relative bg-primary",
  statCardValue: "text-2xl font-bold text-neutral-dark font-miter",
  statCardLabel: "text-md text-neutral font-inter",
  filterContainer: "flex flex-wrap items-center justify-between gap-4 mb-8",
  filterButtonsWrapper: "flex flex-wrap gap-3",
  pathGrid: "grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6",
  pathCard: "bg-neutral-accent rounded-xl shadow-lg border border-neutral-secondary-dark overflow-hidden group cursor-pointer relative",
  pathCardHeader: "p-6 pb-4 relative",
  pathCardTitle: "text-xl font-display font-bold text-neutral font-miter mb-2 group-hover:text-primary transition-colors line-clamp-2",
  pathCardDescription: "text-neutral font-inter text-md line-clamp-1",
  pathCardFooter: "px-6 py-4 bg-neutral-accent-light border-t border-neutral-secondary-dark",
  emptyStateContainer: "text-center py-12",
  emptyStateCard: "bg-neutral-accent rounded-xl p-8 shadow-lg border border-neutral-secondary-dark max-w-md mx-auto relative overflow-hidden",
};

export const getCategoryButtonClasses = (isActive: boolean): string => {
  const baseClasses = "flex items-center px-4 py-2 rounded-lg font-semibold font-inter text-md transition-all relative overflow-hidden gap-2";

  return isActive
    ? `${baseClasses} bg-primary text-white shadow-lg font-bold`
    : `${baseClasses} bg-white text-neutral hover:bg-neutral-accent-light border border-neutral-secondary-dark`;
};