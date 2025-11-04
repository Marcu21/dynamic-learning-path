export const teamStyles = {
  container:        "min-h-screen relative bg-gradient-to-br from-purple-100/50 to-purple-200/40",
  wrapper:          "max-w-7xl mx-auto px-6 py-8 grid grid-cols-12 gap-8 relative z-10",

  // Principal Area
  leftCol:          "col-span-12 lg:col-span-8 space-y-8",
  headerCard:       "bg-white rounded-2xl shadow-md p-6 border border-purple-200",

  pathCard:
    "bg-white rounded-2xl shadow-md p-6 border border-purple-200 " +
    "hover:border-purple-400 hover:shadow-lg hover:scale-105 transition-transform duration-300 cursor-pointer group",
  pathCardActive:   "bg-gradient-to-r from-purple-100 to-purple-200 border-purple-400",

  primaryButton:
    "inline-flex items-center px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-purple-800 " +
    "text-white font-semibold focus:outline-none focus:ring-2 focus:ring-purple-300 transition",
  secondaryButton:
    "inline-flex items-center px-4 py-2 rounded-lg border border-purple-200 text-purple-700 " +
    "hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-200 transition",
  accentButton:
    "inline-flex items-center px-4 py-2 rounded-lg border border-purple-300 text-purple-700 " +
    "hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-200 transition",

  rightCol:         "col-span-12 lg:col-span-4 space-y-6",
  sidebarCard:      "bg-white rounded-2xl shadow-md p-6 border border-purple-200",

  progressBar:      "w-full h-2 bg-purple-100 rounded-full",
  progressFill:     "h-full bg-gradient-to-r from-purple-600 to-purple-800 rounded-full transition-all duration-500",
  statIcon:         "p-3 rounded-xl bg-gradient-to-br from-purple-200 to-purple-100 text-purple-600",
  statIconSubtle:   "p-3 rounded-xl bg-gradient-to-br from-purple-200 to-purple-100 text-purple-600",
  statIconAccent:   "p-3 rounded-xl bg-gradient-to-br from-purple-200 to-purple-100 text-purple-600",

  categoryActive:
    "inline-flex items-center px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-purple-800 " +
    "text-white shadow focus:outline-none focus:ring-2 focus:ring-purple-300 transition",
  categoryInactive:
    "inline-flex items-center px-4 py-2 rounded-lg bg-white text-purple-700 " +
    "border border-purple-200 hover:bg-purple-50 focus:outline-none focus:ring-2 focus:ring-purple-200 transition",
};

export const categories = [
  { id: "all", label: "All Paths", icon: "BookOpen" },
  { id: "in-progress", label: "In Progress", icon: "Play" },
  { id: "completed", label: "Completed", icon: "Trophy" },
];
