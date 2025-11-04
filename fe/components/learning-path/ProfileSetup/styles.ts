import React from "react";

// Default (purple) theme
const defaultStyles = {
  container: "max-w-2xl mx-auto bg-[#edf0f0] rounded-xl shadow-lg p-8",
  headerTitle: "text-3xl font-display font-bold text-neutral-dark flex items-center",
  headerSubtitle: "text-neutral font-sans mt-2 flex items-center",
  headerIcon: "w-4 h-4 mr-2 text-primary",
  stepTitle: "text-2xl font-display font-semibold text-neutral-dark",
  stepSubtitle: "text-neutral font-sans mt-2",
  label: "block font-sans font-bold text-neutral flex items-center",
  labelIcon: "w-4 h-4 mr-2",
  textarea: "w-full p-4 border border-neutral-secondary rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent font-sans text-neutral-dark placeholder-neutral-secondary transition-all duration-300",
  select: "w-full p-4 border border-neutral-secondary rounded-lg focus:ring-2 focus:ring-primary font-sans text-neutral-dark transition-all duration-300",
  checkboxWrapper: "flex items-center space-x-3 transition-all duration-200 hover:scale-[1.01]",
  checkboxInput: "w-4 h-4 text-primary bg-white border border-neutral-secondary rounded focus:ring-primary focus:ring-2",
  sliderContainer: "slider-container",
};

// Team (purple) theme
const teamStyles = {
  ...defaultStyles,
  headerIcon: "w-4 h-4 mr-2 text-purple-600",
  textarea: "w-full p-4 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-sans text-neutral-dark placeholder-neutral-secondary transition-all duration-300",
  select: "w-full p-4 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 font-sans text-neutral-dark transition-all duration-300",
  checkboxInput: "w-4 h-4 text-purple-600 bg-white border border-purple-200 rounded focus:ring-purple-500 focus:ring-2",
};

export const getProfileSetupStyles = (theme: 'default' | 'team' = 'default') =>
  theme === 'team' ? teamStyles : defaultStyles;

export const getProgressIndicatorClasses = (isActive: boolean, theme: 'default' | 'team' = 'default'): string => {
  const baseClasses = "absolute top-1/2 z-20 w-3 h-3 rounded-full border-2 -translate-y-1/2";
  if (theme === 'team') {
    return isActive
      ? `${baseClasses} bg-white border-purple-600`
      : `${baseClasses} bg-white border-purple-200`;
  }
  return isActive
    ? `${baseClasses} bg-white border-primary`
    : `${baseClasses} bg-white border-neutral-secondary-light`;
};

export const getButtonVariant = (isActive: boolean): 'primary' | 'hollow' => {
  return isActive ? "primary" : "hollow";
};

export const getSliderStyle = (value: number | undefined): React.CSSProperties => {
  const progress = (((value || 30) - 15) / (360 - 15)) * 100;
  return {
    "--slider-progress": `${progress}%`,
  } as React.CSSProperties;
};