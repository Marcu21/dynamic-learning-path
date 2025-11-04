"use client";

import { createContext, useContext, useState, useCallback, useMemo, useEffect, useRef, type ReactNode } from "react";
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { useRouter } from "next/router";
import type { Notification as AppNotification } from '@/types/notifications';
import { NotificationContextType, SelectionEvent, GenerationCompletionEvent } from '@/context/types';
import { webSocketManager } from "@/lib/websocketManager";

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const playNotificationSound = () => {
  const audio = new Audio('/notification.mp3');
  audio.play().catch();
};

export const NotificationProvider = ({ children }: { children: ReactNode }) => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [isSoundEnabled, setIsSoundEnabled] = useState(true);
  const [selectionEvent, setSelectionEvent] = useState<SelectionEvent | null>(null);
  const [generationCompletionEvent, setGenerationCompletionEvent] = useState<GenerationCompletionEvent | null>(null);
  const taskCompletionHandlersRef = useRef<Array<(taskId: string, result: any) => void>>([]);
  const { isAuthenticated, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const fetchInitialNotifications = async () => {
      if (isAuthenticated) {
        try {
          const response = await api.getNotifications({ include_read: false, per_page: 50 });

          const notificationsArray = Array.isArray(response.notifications) ? response.notifications : [];
          const fetchedNotifications = notificationsArray.map((n: any) => {
            const createdAtString = n.created_at;
            const utcDate = createdAtString
              ? new Date(createdAtString.endsWith('Z') ? createdAtString : createdAtString.replace(' ', 'T') + 'Z')
              : new Date();

            return {
              id: n.id.toString(),
              message: n.title ? `${n.title}: ${n.message}` : n.message,
              pathId: n.learning_path_id,
              teamId: n.team_id,
              date: utcDate,
              read: n.is_read,
            };
          });

          setNotifications(fetchedNotifications);
        } catch (error) {}
      }
    };

    fetchInitialNotifications();
  }, [isAuthenticated]);

  const addNotification = useCallback((message: string, pathId?: number, teamId?: string) => {
    const newNotification: AppNotification = {
      id: uuidv4(), message, pathId, teamId, date: new Date(), read: false
    };
    setNotifications(prev => [newNotification, ...prev]);
    if (isSoundEnabled) {
      playNotificationSound();
    }
  }, [isSoundEnabled]);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      return;
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const notificationsWsUrl = baseUrl.replace(/^https?:\/\//, 'ws://') + `/api/v1/notifications/ws/notifications?token=${encodeURIComponent(token)}`;

    const manager = webSocketManager.getInstance(notificationsWsUrl);

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'notification' && data.notification?.type === 'task_completed' && data.notification?.result?.learning_path_id) {

          const notification = data.notification;
          const result = data.notification.result;
          const teamId = result.team_id || notification.team_id || notification.learning_path?.team_id;

          setGenerationCompletionEvent({learning_path: { id: result.learning_path_id, ...result }, teamId: teamId, timestamp: Date.now()});

          const newNotification: AppNotification = {
            id: data.notification.id?.toString() || uuidv4(),
            message: data.notification.message,
            pathId: result.learning_path_id,
            teamId: teamId,
            date: new Date(data.notification.completion_time || Date.now()),
            read: false,
          };
          setNotifications(prev => [newNotification, ...prev]);
          if (isSoundEnabled) playNotificationSound();

        } else if (data.type === 'notification') {
          const notification = data.notification;
          const regularNotification: AppNotification = {
            id: notification.id?.toString() || uuidv4(),
            message: notification.title ? `${notification.title}: ${notification.message}` : notification.message,
            pathId: notification.learning_path_id,
            teamId: notification.team_id,
            date: new Date(notification.created_at || Date.now()),
            read: notification.is_read || false,
          };
          setNotifications(prev => [regularNotification, ...prev]);
          if (isSoundEnabled) playNotificationSound();
        }
      } catch (error) {}
    };

    manager.addListener(handleMessage);

    return () => {
      manager.removeListener(handleMessage);
    };
  }, [isAuthenticated, token, isSoundEnabled]);


  const markAllAsRead = useCallback(async (): Promise<void> => {
    const unreadIds = notifications.filter(n => !n.read).map(n => parseInt(n.id, 10)).filter(id => !isNaN(id));
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    try {
        if (unreadIds.length > 0) {
            await api.markAllNotificationsAsRead();
        }
    } catch (error) {}
  }, [notifications]);

  const markAsRead = useCallback(async (notificationId: string): Promise<void> => {
    setNotifications(prev =>
      prev.map(n => (n.id === notificationId ? { ...n, read: true } : n))
    );
    try {
      const numericId = parseInt(notificationId, 10);
      if (!isNaN(numericId)) {
        await api.markNotificationAsRead(numericId);
      }
    } catch (error) {}
  }, []);

  const toggleSound = useCallback(() => setIsSoundEnabled(prev => !prev), []);

  const selectPath = useCallback(async (pathId: number, teamId?: string): Promise<void> => {
    try {
        await api.getLearningPath(pathId);
        if (teamId) {
            await api.getTeam(teamId);
        }
        setSelectionEvent({ pathId, teamId, timestamp: Date.now() });
    } catch (error: any) {
        const staleNotification = notifications.find(n => n.pathId === pathId && (teamId ? n.teamId === teamId : true));
        if (staleNotification) {
            markAsRead(staleNotification.id);
        }
        router.push({
            pathname: '/_error',
            query: {
                statusCode: 404,
                message: 'The learning path or team you are looking for no longer exists. It may have been deleted.'
            }
        });
    }
  }, [notifications, markAsRead, router]);

  const clearSelection = useCallback(() => {
    setSelectionEvent(null);
  }, []);

  const registerTaskCompletionHandler = useCallback((handler: (taskId: string, result: any) => void) => {
    taskCompletionHandlersRef.current.push(handler);
  }, []);

  const clearGenerationEvent = useCallback(() => {
    setGenerationCompletionEvent(null);
  }, []);

  const unreadCount = useMemo(() => {
    return notifications.filter(n => !n.read).length;
  }, [notifications]);

  const value: NotificationContextType = useMemo(() => ({
    notifications,
    unreadCount,
    addNotification,
    markAllAsRead,
    markAsRead,
    selectionEvent,
    selectPath,
    clearSelection,
    isSoundEnabled,
    toggleSound,
    onTaskCompleted: undefined,
    registerTaskCompletionHandler,
    generationCompletionEvent,
    clearGenerationEvent,
  }), [
    notifications, unreadCount, selectionEvent, addNotification, markAllAsRead,
    markAsRead, selectPath, clearSelection, isSoundEnabled, toggleSound,
    registerTaskCompletionHandler, generationCompletionEvent, clearGenerationEvent,
  ]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within a NotificationProvider");
  }
  return context;
};