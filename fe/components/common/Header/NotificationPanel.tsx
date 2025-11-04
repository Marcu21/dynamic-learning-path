"use client"

import { motion } from "framer-motion"
import {BellOff, Clock, CheckCircle2, Bell, VolumeX, Volume2} from "lucide-react"
import { Notification } from "@/types/notifications"
import { useNotifications } from "@/context/NotificationContext"
import { NotificationPanelProps } from "@/components/common/Header/types"

// Helper function to display relative time
const timeAgo = (date: Date): string => {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)
  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + " years ago"
  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + " months ago"
  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + " days ago"
  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + " hours ago"
  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + " minutes ago"
  return "just now"
}

export const NotificationPanel = ({ onClose }: NotificationPanelProps) => {
  const { notifications, selectPath, markAllAsRead, markAsRead, unreadCount, isSoundEnabled, toggleSound } = useNotifications();

  const handleNotificationClick = (notification: Notification) => {
    if (notification.pathId) {
      // MODIFICATION: Pass the teamId along with the pathId
      selectPath(notification.pathId, notification.teamId);
      markAsRead(notification.id);
      onClose();
    }
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  return (
    <motion.div
      className="absolute top-16 right-0 w-96 bg-gradient-to-br from-white to-gray-50 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/40 overflow-hidden z-50 origin-top-right"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      <div className="bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-700 p-6 text-white">

        {/* Title */}
        <h3 className="font-bold text-lg">Notification Center</h3>

        {/* Info and actions */}
        <div className="flex justify-between items-center">
          {/* Notification Count */}
          <p className="text-white/80 text-sm">
            {unreadCount > 0 ? `${unreadCount} new notification${unreadCount !== 1 ? 's' : ''}` : "No new notifications"}
          </p>

          {/* Right panel */}
          <div className="flex items-center gap-4">
            {unreadCount > 0 && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleMarkAllAsRead}
                className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-xs font-semibold transition-colors backdrop-blur-sm"
              >
                Mark All Read
              </motion.button>
            )}
            <motion.button
              onClick={toggleSound}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="w-8 h-8 bg-white/20 hover:bg-white/30 transition-colors rounded-full flex items-center justify-center cursor-pointer"
              title={isSoundEnabled ? "Mute sounds" : "Unmute sounds"}
            >
              <motion.div
                animate={{ rotate: unreadCount > 0 ? [0, 15, -15, 0] : 0 }}
                transition={{ duration: 0.5, repeat: unreadCount > 0 ? Number.POSITIVE_INFINITY : 0, repeatDelay: 3 }}
              >
                {isSoundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </motion.div>
            </motion.button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-h-96 overflow-y-auto custom-scrollbar">
        {notifications.length > 0 ? (
          <div className="p-4 space-y-2">
            {notifications.map((notification, index) => {
              const isUnread = !notification.read;

              return (
                <motion.div
                  key={notification.id}
                  className={`
                    group relative p-4 rounded-2xl cursor-pointer transition-all duration-200 hover:bg-gray-50/80
                    ${isUnread 
                      ? "bg-gradient-to-r from-blue-50/80 to-purple-50/80 border-l-4 border-l-blue-500 shadow-sm" 
                      : "bg-white/50 hover:bg-gray-50"
                    }
                  `}
                  whileHover={{ scale: 1.02, x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleNotificationClick(notification)}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="flex items-start gap-3">
                    <div className={`
                      w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 transition-colors
                      ${isUnread 
                        ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg" 
                        : "bg-gray-200 text-gray-600"
                      }
                    `}>
                      <Bell className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className={`
                        text-sm leading-relaxed break-words
                        ${isUnread ? "text-gray-900 font-medium" : "text-gray-600"}
                      `}>
                        {notification.message}
                      </p>
                      
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3 text-gray-400" />
                          <span className="text-xs text-gray-500">
                            {timeAgo(notification.date)}
                          </span>
                        </div>

                        {isUnread && (
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              markAsRead(notification.id);
                            }}
                            className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-full transition-colors"
                            title="Mark as read"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </motion.button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Unread indicator */}
                  {isUnread && (
                    <motion.div
                      className="absolute top-3 right-3 w-2 h-2 bg-blue-500 rounded-full shadow-sm"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3, type: "spring", stiffness: 500 }}
                    />
                  )}
                </motion.div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
                <BellOff className="w-8 h-8 text-gray-400" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">All caught up!</h4>
                <p className="text-sm text-gray-500">No new notifications at the moment.</p>
              </div>
            </motion.div>
          </div>
        )}
      </div>

      {/* Footer with statistics */}
      {notifications.length > 0 && (
        <div className="border-t border-gray-200/50 p-4 bg-gradient-to-r from-gray-50/50 to-white/50">
          <p className="text-xs text-center text-gray-500">
            {notifications.length} total notification{notifications.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}
    </motion.div>
  );
};