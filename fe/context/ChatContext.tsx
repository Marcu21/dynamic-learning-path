'use client';

import React, { createContext, useContext, useState } from 'react';
import { LocationKind, ChatContextValue, ChatProviderProps } from "@/context/types";

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

const LOCATION_PRIORITY: Record<LocationKind, number> = {
  dashboard: 0,
  learning_path: 1,
  module: 2,
  quiz: 3,
  quiz_attempt_active: 4,
  review_answers: 5,
};

export const ChatProvider: React.FC<ChatProviderProps> = ({
  children,
  initialLocation = 'dashboard',
}) => {
  const [currentLocation, setCurrentLocation] = useState<LocationKind>(initialLocation);
  const [learningPathId, setLearningPathId] = useState<number | undefined>();
  const [moduleId, setModuleId] = useState<number | undefined>();
  const [quizId, setQuizId] = useState<number | undefined>();
  const [quizAttemptId, setQuizAttemptId] = useState<number | undefined>();

  const setLocation = (location: LocationKind) => {
    setCurrentLocation(location);

    // Reset context IDs when location changes to certain states
    if (location === 'dashboard') {
      setLearningPathId(undefined);
      setModuleId(undefined);
      setQuizId(undefined);
      setQuizAttemptId(undefined);
    } else if (location === 'learning_path') {
      setModuleId(undefined);
      setQuizId(undefined);
      setQuizAttemptId(undefined);
    } else if (location === 'module') {
      setQuizId(undefined);
      setQuizAttemptId(undefined);
    }
  };

  const updateChatContext = (context: Partial<ChatContextValue>) => {
    setCurrentLocation((prevLoc) => {
      const incomingLoc = (context.currentLocation ?? prevLoc) as LocationKind;

      const prevP = LOCATION_PRIORITY[prevLoc];
      const nextP = LOCATION_PRIORITY[incomingLoc];

      if (nextP < prevP) {
        return prevLoc;
      }

      if (incomingLoc !== prevLoc) {
        if (incomingLoc === 'dashboard') {
          setLearningPathId(undefined);
          setModuleId(undefined);
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        } else if (incomingLoc === 'learning_path') {
          setModuleId(undefined);
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        } else if (incomingLoc === 'module') {
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        }
      }

      if (context.learningPathId !== undefined) setLearningPathId(context.learningPathId);
      if (context.moduleId !== undefined) setModuleId(context.moduleId);
      if (context.quizId !== undefined) setQuizId(context.quizId);
      if (context.quizAttemptId !== undefined) setQuizAttemptId(context.quizAttemptId);

      return incomingLoc;
    });
  };

  const updateChatContextAllowDowngrade = (context: Partial<ChatContextValue>) => {
    setCurrentLocation((prevLoc) => {
      const incomingLoc = (context.currentLocation ?? prevLoc) as LocationKind;

      if (incomingLoc !== prevLoc) {
        if (incomingLoc === 'dashboard') {
          setLearningPathId(undefined);
          setModuleId(undefined);
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        } else if (incomingLoc === 'learning_path') {
          setModuleId(undefined);
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        } else if (incomingLoc === 'module') {
          setQuizId(undefined);
          setQuizAttemptId(undefined);
        }
      }

      if ('learningPathId' in context) setLearningPathId(context.learningPathId);
      if ('moduleId' in context) setModuleId(context.moduleId);
      if ('quizId' in context) setQuizId(context.quizId);
      if ('quizAttemptId' in context) setQuizAttemptId(context.quizAttemptId);

      return incomingLoc;
    });
  };

  const value: ChatContextValue = {
    currentLocation,
    learningPathId,
    moduleId,
    quizId,
    quizAttemptId,
    setLocation,
    setLearningPathId,
    setModuleId,
    setQuizId,
    setQuizAttemptId,
    updateChatContext,
    updateChatContextAllowDowngrade, // ← NEW in context value
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export const useChatContext = (): ChatContextValue => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};

// Hook for updating chat context based on current location
export const useChatLocationUpdater = () => {
  const {
    updateChatContext,
    updateChatContextAllowDowngrade,
  } = useChatContext();

  return {
    // Dashboard
    setDashboardContext: () => {
      updateChatContext({ currentLocation: 'dashboard' });
    },

    // Learning path
    setLearningPathContext: (learningPathId: number) => {
      updateChatContext({
        currentLocation: 'learning_path',
        learningPathId,
        moduleId: undefined,
        quizId: undefined,
        quizAttemptId: undefined,
      });
    },

    // Module
    setModuleContext: (learningPathId: number, moduleId: number) => {
      updateChatContext({
        currentLocation: 'module',
        learningPathId,
        moduleId,
        quizId: undefined,
        quizAttemptId: undefined,
      });
    },

    // QUIZ
    setQuizContext: (learningPathId: number, moduleId: number, quizId: number) => {
      updateChatContext({
        currentLocation: 'quiz',
        learningPathId,
        moduleId,
        quizId,
        quizAttemptId: undefined,
      });
    },

    // Quiz attempt active
    setQuizAttemptContext: (
      learningPathId: number,
      moduleId: number,
      quizId: number,
      quizAttemptId: number
    ) => {
      updateChatContext({
        currentLocation: 'quiz_attempt_active',
        learningPathId,
        moduleId,
        quizId,
        quizAttemptId,
      });
    },

    // Review answers
    setReviewAnswersContext: (
      learningPathId: number,
      moduleId: number,
      quizId: number,
      quizAttemptId: number
    ) => {
      updateChatContext({
        currentLocation: 'review_answers',
        learningPathId,
        moduleId,
        quizId,
        quizAttemptId,
      });
    },

    setLearningPathContextForce: (learningPathId: number) => {
      updateChatContextAllowDowngrade({
        currentLocation: 'learning_path',
        learningPathId,
        moduleId: undefined,
        quizId: undefined,
        quizAttemptId: undefined,
      });
    },

    setModuleContextForce: (learningPathId: number, moduleId: number) => {
      updateChatContextAllowDowngrade({
        currentLocation: 'module',
        learningPathId,
        moduleId,
        quizId: undefined,
        quizAttemptId: undefined,
      });
    },
    setQuizContextForce: (learningPathId: number, moduleId: number, quizId?: number) => {
  updateChatContextAllowDowngrade({
    currentLocation: 'quiz',
    learningPathId,
    moduleId,
    quizId,
    quizAttemptId: undefined,
  });
},
  };
};