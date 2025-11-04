'use client';

import React from 'react';
import {ChatAssistant} from './ChatAssistant';
import {useChatContext} from '@/context/ChatContext';
import {IntegratedChatAssistantProps} from "@/components/chat/types";

/**
 * This component automatically uses the chat context to provide
 * location-aware chat assistance. It should be placed at the app level
 * and will automatically adapt based on where the user is.
 */
export const IntegratedChatAssistant: React.FC<IntegratedChatAssistantProps> = ({
  userId,
  className,
  location: locationOverride,
  learningPathId: lpIdOverride,
  moduleId: moduleOverride,
  quizId: quizOverride,
  quizAttemptId: attemptOverride,
  teamId: teamIdOverride
}) => {
  const context = useChatContext();

  // Prioritize overrides, then context, then fallbacks
  const location = locationOverride ?? context.currentLocation;
  const learningPathId = lpIdOverride ?? context.learningPathId;
  const moduleId = moduleOverride ?? context.moduleId;
  const quizId = quizOverride ?? context.quizId;
  const quizAttemptId = attemptOverride ?? context.quizAttemptId;
  return (
    <ChatAssistant
      userId={userId}
      location={location}
      learningPathId={learningPathId}
      moduleId={moduleId}
      quizId={quizId}
      quizAttemptId={quizAttemptId}
      teamId={teamIdOverride}
      className={className}
    />
  );
};