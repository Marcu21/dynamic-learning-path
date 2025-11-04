"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {ChevronRight, ChevronLeft, Zap, Sparkles, Target, Brain, Clock, AlertTriangle} from "lucide-react";
import type { UserProfile, LearningGoal } from "@/types/user";
import { Button } from "@/components/common/Button";
import { spring, itemVariants, stepVariants } from "./animations";
import { getProfileSetupStyles, getProgressIndicatorClasses, getButtonVariant, getSliderStyle } from "./styles";

const totalSteps = 3;

const platformOptions: Record<string, string[]> = {
  reading: ["Google Books", "Research Papers"],
  visual: ["YouTube"],
  auditory: ["Spotify"],
  kinesthetic: ["Codeforces"],
};



const ErrorMessage = ({ message }: { message?: string }) => (
  <AnimatePresence>
    {message && (
      <motion.div
        initial={{ opacity: 0, y: -5 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -5 }}
        transition={{ duration: 0.2 }}
        className="flex items-center text-sm text-red-600 space-x-1.5 pt-1"
      >
        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
        <span>{message}</span>
      </motion.div>
    )}
  </AnimatePresence>
);

export default function ProfileSetup({
  onComplete,
  onCancel,
  username,
  theme = 'default',
}: {
  onComplete: (p: UserProfile, g: LearningGoal) => void;
  onCancel?: () => void;
  username?: string;
  theme?: 'default' | 'team';
}) {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<Partial<UserProfile & { learning_styles?: string[] }>>({ learning_styles: [] });
  const [goal, setGoal] = useState<Partial<LearningGoal>>({});
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const styles = getProfileSetupStyles(theme);

  const clearErrorForKey = (key: string) => {
    setErrors(prev => {
      if (!prev[key]) return prev;
      const newErrors = { ...prev };
      delete newErrors[key];
      return newErrors;
    });
  };

  const validateStep = (currentStep: number): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (currentStep === 1) {
      if (!goal.goal || goal.goal.trim() === "") newErrors.goal = "Please describe your learning goal.";
      if (!goal.priority || goal.priority === "") newErrors.priority = "Please select a priority level.";
    }

    if (currentStep === 2) {
      if (!profile.experience_level) newErrors.experience = "Please select your experience level.";

      const selectedStyles = profile.learning_styles || [];
      const selectedPlatforms = profile.platforms || [];

      if (selectedStyles.length === 0) {
        newErrors.styles = "Please select at least one learning style.";
      } else {
        const allStylesHavePlatforms = selectedStyles.every(style => {
          const availablePlatforms = platformOptions[style] || [];
          return availablePlatforms.some(platform => selectedPlatforms.includes(platform));
        });

        if (!allStylesHavePlatforms) {
          newErrors.platforms = "Each learning style must have at least one platform selected.";
        }
      }
    }

    if (currentStep === 3) {
      if (!profile.available_time) {
        newErrors.time = "Please set your available study time.";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(s => s + 1);
    }
  };

  const handlePrevious = () => {
    setErrors({});
    setStep(s => s - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) {
        return;
    }

    try {
      const nameToUse = username || "Guest_" + Math.floor(Math.random() * 10000);
      const completeProfile: UserProfile = { ...profile as UserProfile, name: nameToUse };
      const completeGoal: LearningGoal = goal as LearningGoal;
      onComplete(completeProfile, completeGoal);
    } catch (error) {
      alert("Something went wrong: " + (error as Error).message);
    }
  };

  // Progress bar should reach the center of the circles
  const progressArr = [0, 34.5, 67.5];
  const progress = progressArr[step - 1];
  const selectedLearningStyles = profile.learning_styles || [];


  return (
    <div className={styles.container}>
      {/* PROGRESS BAR */}
      <motion.div className="mb-8" variants={itemVariants}>
        <div className="flex items-center justify-between gap-14">
          <motion.div whileHover={{ scale: 1.02 }} transition={spring}>
            <h2 className={styles.headerTitle}>
              <motion.div
                className="mr-3"
                transition={{ duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
              >
                <Sparkles className="w-8 h-8 text-primary" />
              </motion.div>
              Create Your Learning Journey
            </h2>
            <p className={styles.headerSubtitle}>
              <Brain className={styles.headerIcon} />
              AI will personalize your path
            </p>
          </motion.div>

          <motion.div
            className="text-right"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
          >
          </motion.div>
        </div>

        <div className="text-center font-bold mb-2 mt-2">
            <span className={styles.stepSubtitle}>
              Step {step} of {totalSteps}
            </span>
        </div>

        <div className="relative w-full">
          <div className={theme === 'team' ? "w-full h-3 bg-purple-100 rounded-full" : "w-full h-3 bg-neutral-secondary-light rounded-full"} />
          <motion.div
            className={theme === 'team' ? "absolute top-0 left-0 h-3 bg-purple-600 rounded-full z-10" : "absolute top-0 left-0 h-3 bg-primary rounded-full z-10"}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
          </motion.div>
          {[33, 66].map((pos, i) => (
            <motion.div
              key={i}
              className={getProgressIndicatorClasses(progress >= pos, theme)}
              style={{ left: `${pos}%` }}
              animate={
                progress === pos
                  ? {
                      scale: [1, 1.3, 1],
                      boxShadow: [
                        theme === 'team'
                          ? "0 0 0 0 rgba(147, 51, 234, 0.7)"
                          : "0 0 0 0 rgba(129, 28, 221, 0.7)",
                        theme === 'team'
                          ? "0 0 0 8px rgba(147, 51, 234, 0)"
                          : "0 0 0 8px rgba(129, 28, 221, 0)",
                        theme === 'team'
                          ? "0 0 0 0 rgba(147, 51, 234, 0.7)"
                          : "0 0 0 0 rgba(129, 28, 221, 0.7)",
                      ],
                    }
                  : {}
              }
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            />
          ))}
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.div key={step} variants={stepVariants} initial="hidden" animate="visible" exit="exit">
          {step === 1 && (
            <motion.div className="space-y-6" variants={itemVariants}>
              <motion.div className="text-center mb-8" whileHover={{ scale: 1.02 }} transition={spring}>
                <motion.div
                  className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4"
                  animate={{
                    boxShadow: [
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                      "0 0 40px rgba(129, 28, 221, 0.5)",
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                    ],
                  }}
                  transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                >
                  <Target className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className={styles.stepTitle}>What's your learning goal?</h3>
                <p className={styles.stepSubtitle}>Tell us what you want to achieve</p>
              </motion.div>

              <motion.div className="space-y-2" whileHover={{ scale: 1.01 }} transition={spring}>
                <label className={styles.label}>
                  <Sparkles className={`${styles.labelIcon} text-primary`} />
                  Learning Goal
                </label>
                <motion.textarea
                  value={goal.goal || ""}
                  onChange={(e) => {
                    setGoal({ ...goal, goal: e.target.value });
                    clearErrorForKey('goal');
                  }}
                  className={`${styles.textarea} ${errors.goal ? 'border-red-500' : ''}`}
                  placeholder="e.g., Learn Python for data science..."
                  rows={4}
                />
                <ErrorMessage message={errors.goal} />
              </motion.div>

              <motion.div className="space-y-2" whileHover={{ scale: 1.01 }} transition={spring}>
                <label className={styles.label}>
                  <Zap className={`${styles.labelIcon} text-warning`} />
                  Priority Level
                </label>
                <motion.select
                  value={goal.priority || ""}
                  onChange={(e) => {
                    setGoal({ ...goal, priority: e.target.value });
                    clearErrorForKey('priority');
                  }}
                  className={`${styles.select} ${errors.priority ? 'border-red-500' : ''}`}
                >
                  <option value="">Select priority level</option>
                  <option value="low">🌱 Low – Learning for fun</option>
                  <option value="medium">🚀 Medium – Personal development</option>
                  <option value="high">⚡ High – Career advancement</option>
                </motion.select>
                <ErrorMessage message={errors.priority} />
              </motion.div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div className="space-y-6" variants={itemVariants}>
              <motion.div className="text-center mb-8" whileHover={{ scale: 1.02 }} transition={spring}>
                <motion.div
                  className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4"
                  animate={{
                    boxShadow: [
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                      "0 0 40px rgba(129, 28, 221, 0.5)",
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                    ],
                  }}
                  transition={{
                    rotate: { duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "linear" },
                    boxShadow: { duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" },
                  }}
                >
                  <Brain className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className={styles.stepTitle}>Tell us about your learning style</h3>
                <p className={styles.stepSubtitle}>Help us personalize your experience</p>
              </motion.div>

              <motion.div className="space-y-2" variants={itemVariants}>
                <label className={styles.label}>
                  <Target className={`${styles.labelIcon} text-success`} />
                  Experience Level
                </label>
                <div className="grid grid-cols-3 gap-4">
                  {["beginner", "intermediate", "advanced"].map((lvl, index) => (
                    <motion.div key={lvl} whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }} transition={spring}>
                      <Button
                        variant={getButtonVariant(profile.experience_level === lvl)}
                        onClick={() => {
                          setProfile({ ...profile, experience_level: lvl });
                          clearErrorForKey('experience');
                        }}
                        className="w-full capitalize font-semibold"
                      >
                        {["🌱", "🚀", "⚡"][index]} {lvl}
                      </Button>
                    </motion.div>
                  ))}
                </div>
                <ErrorMessage message={errors.experience} />
              </motion.div>

              <motion.div className="space-y-2" variants={itemVariants}>
                <label className={styles.label}>
                  <Sparkles className={`${styles.labelIcon} text-primary`} />
                  Preferred Learning Styles & Platforms
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { id: "visual", label: "Visual", icon: "👁️" },
                    { id: "auditory", label: "Auditory", icon: "🎧" },
                    { id: "kinesthetic", label: "Hands-on", icon: "✋" },
                    { id: "reading", label: "Reading", icon: "📚" },
                  ].map((style) => {
                    const isActive = selectedLearningStyles.includes(style.id);
                    return (
                      <motion.div key={style.id} whileHover={{ scale: 1.05, y: -2 }} whileTap={{ scale: 0.95 }} transition={spring}>
                        <Button
                          variant={isActive ? "primary" : "hollow"}
                          onClick={() => {
                            setProfile((prev) => {
                              const prevStyles = prev.learning_styles || [];
                              return {
                                ...prev,
                                learning_styles: isActive
                                  ? prevStyles.filter((s) => s !== style.id)
                                  : [...prevStyles, style.id],
                                // Reset platforms if no styles selected
                                platforms: prevStyles.length === 1 && isActive ? [] : prev.platforms || [],
                              };
                            });
                          }}
                          className={`w-full text-left flex items-center font-semibold p-4 ${isActive ? 'ring-2 ring-primary' : ''}`}
                        >
                          <span className="text-2xl">{style.icon}</span>
                          <span className="font-sans">{style.label}</span>
                        </Button>
                        {/* Show platforms for this style if selected */}
                        {isActive && (
                          <div className="ml-2 mt-2 space-y-1">
                            <div className="text-md text-neutral-dark mb-1">Platforms for {style.label}:</div>
                            {(platformOptions[style.id] || []).map((plat) => (
                              <label key={plat} className={styles.checkboxWrapper}>
                                <input
                                  type="checkbox"
                                  className={styles.checkboxInput}
                                  checked={profile.platforms?.includes(plat) || false}
                                  onChange={(e) => {
                                    const prev = profile.platforms || [];
                                    setProfile({
                                      ...profile,
                                      platforms: e.target.checked ? [...prev, plat] : prev.filter((p) => p !== plat),
                                    });
                                  }}
                                  // Disable if already selected by another style (to avoid duplicate checkboxes)
                                />
                                <span className="font-sans text-neutral-dark">{plat}</span>
                              </label>
                            ))}
                          </div>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
                <ErrorMessage message={errors.styles || errors.platforms} />
              </motion.div>
            </motion.div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
             <motion.div className="space-y-6" variants={itemVariants}>
              <motion.div className="text-center mb-8" whileHover={{ scale: 1.02 }} transition={spring}>
                <motion.div
                  className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4"
                  animate={{
                    scale: [1, 1.1, 1],
                    boxShadow: [
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                      "0 0 40px rgba(129, 28, 221, 0.5)",
                      "0 0 20px rgba(129, 28, 221, 0.3)",
                    ],
                  }}
                  transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                >
                  <Clock className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className={styles.stepTitle}>Customize your experience</h3>
                <p className={styles.stepSubtitle}>Set your learning schedule</p>
              </motion.div>

              <div>
                    <label className={styles.label}>
                    Available study time per day
                    </label>
                    <div className={styles.sliderContainer} style={getSliderStyle(profile.available_time)}>
                    <input
                      type="range"
                      min={15}
                      max={360}
                      step={5}
                      value={profile.available_time || 30}
                      onChange={(e) => {
                        setProfile({ ...profile, available_time: Number(e.currentTarget.value) });
                        clearErrorForKey('time');
                      }}
                    />
                    <div className="slider-tooltip">{profile.available_time || 30} min</div>
                    </div>
                    <ErrorMessage message={errors.time} />
                </div>
             </motion.div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* NAVIGATION BUTTONS */}
      <div className="flex justify-between mt-8">
        {step === 1 ? (
          <Button variant="hollow" onClick={onCancel} disabled={!onCancel}>
            Cancel
          </Button>
        ) : (
          <Button variant="hollow" onClick={handlePrevious}>
            <ChevronLeft className="w-4 h-4" /> Previous
          </Button>
        )}

        {step < totalSteps ? (
          <Button variant="primary" onClick={handleNext} className="flex items-center">
            Next <ChevronRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button variant="success" onClick={handleSubmit} className="flex items-center">
            <Zap className="w-4 h-4" /> Generate My Path
          </Button>
        )}
      </div>
    </div>
  );
}