"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

export type SortOption = {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  getValue: (path: any) => any;
};

export type SortOrder = 'asc' | 'desc';

export interface SortComboboxProps {
  selectedSort: string;
  sortOrder: SortOrder;
  onSortChange: (sortId: string, order: SortOrder) => void;
  sortOptions: SortOption[];
}

const SortCombobox: React.FC<SortComboboxProps> = ({
  selectedSort,
  sortOrder,
  onSortChange,
  sortOptions
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const selectedOption = sortOptions.find(opt => opt.id === selectedSort) || sortOptions[0];

  const handleSortChange = (sortId: string) => {
    if (sortId === selectedSort) {
      // Toggle order if same sort is selected
      onSortChange(sortId, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to ascending for new sort
      onSortChange(sortId, 'asc');
    }
    setIsOpen(false);
  };

  const getSortIcon = () => {
    if (sortOrder === 'asc') return <ArrowUp className="w-4 h-4" />;
    if (sortOrder === 'desc') return <ArrowDown className="w-4 h-4" />;
    return <ArrowUpDown className="w-4 h-4" />;
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center px-4 py-2 rounded-lg font-semibold font-inter text-md transition-all relative overflow-hidden gap-2 bg-white text-neutral hover:bg-neutral-accent-light border border-neutral-secondary-dark"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <selectedOption.icon className="w-4 h-4" />
        <span>Sort by {selectedOption.label}</span>
        {getSortIcon()}
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4 text-neutral-secondary-light" />
        </motion.div>
      </motion.button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              className="absolute top-full left-0 mt-2 bg-white rounded-xl shadow-xl border border-neutral-accent-light z-50 min-w-48"
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              {sortOptions.map((option, index) => (
                <motion.button
                  key={option.id}
                  onClick={() => handleSortChange(option.id)}
                  className={`w-full p-3 text-left transition-colors flex items-center justify-between group hover:bg-neutral-accent-light ${
                    index !== sortOptions.length - 1 ? 'border-b border-neutral-accent-light' : ''
                  } ${
                    selectedSort === option.id ? 'bg-primary-light text-primary' : 'text-neutral-dark'
                  }`}
                  whileHover={{ x: 4 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="flex items-center space-x-3">
                    <option.icon className="w-4 h-4" />
                    <span className="font-medium">{option.label}</span>
                  </div>
                  {selectedSort === option.id && (
                    <div className="flex items-center space-x-1">
                      {getSortIcon()}
                    </div>
                  )}
                </motion.button>
              ))}
            </motion.div>
            {/* Click-away overlay */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SortCombobox;