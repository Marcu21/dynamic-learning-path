"use client"

import React, {useMemo} from "react"
import { useState, useRef, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { usePathname } from "next/navigation"
import { MessageCircle, X, Send, Loader2, User, Bot, Sparkles, ArrowDown, AlertTriangle } from "lucide-react"
import { chatApi } from "@/lib/chatApi"
import { ChatRequest} from "@/lib/types"
import { useOnClickOutside } from "@/hooks/useOnClickOutside"
import { ChatMessage, ChatAssistantProps, LocationContext } from "@/components/chat/types"

const renderFormattedText = (text: string) => {
  const parts = text.split(/(\*\*.*?\*\*)/g)
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-inherit">
          {part.substring(2, part.length - 2)}
        </strong>
      )
    }
    return part
  })
}

export const ChatAssistant: React.FC<ChatAssistantProps> = ({
  userId,
  location,
  learningPathId,
  moduleId,
  quizId,
  quizAttemptId,
  teamId,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [, setStreamingMessageId] = useState<string | null>(
    null,
  )
  const [statusMessage, setStatusMessage] = useState("")
  const [userHasScrolledUp, setUserHasScrolledUp] = useState(false)
  const [showScrollButton, setShowScrollButton] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null!)
  const [inputError, setInputError] = useState<string | null>(null)
  const initialHeight = Math.min(Math.max(window.innerHeight * 0.75, 450), 600)

  const [size, setSize] = useState<{ width: number; height: number }>({
    width: 420,
    height: initialHeight,
  })
  const isResizingRef = useRef(false)
  const startMousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const startSizeRef = useRef<{ width: number; height: number }>({
    width: 420,
    height: initialHeight,
  })


  const pathname = usePathname()

  const routeLocationOverride = useMemo<LocationContext | null>(() => {
    if (!pathname) return null
    if (pathname === "/" || pathname.startsWith("/dashboard")) return "dashboard"
    return null
  }, [pathname])

  const computeLocation = ({
  location,
  learningPathId,
  moduleId,
  quizId,
  quizAttemptId,
}: {
  location?: string | LocationContext
  learningPathId?: number
  moduleId?: number
  quizId?: number
  quizAttemptId?: number
}): LocationContext => {
  if (location && location !== "auto") {
    return location as LocationContext
  }

  // 1) fallback: for active attempt
  if (quizAttemptId) return "quiz_attempt_active"
  // 2) fallback: for quiz id
  if (quizId) return "quiz"
  // 3) fallback: derive from rest
  if (moduleId) return "module"
  if (learningPathId) return "learning_path"
  return "dashboard"
}


const computedLocation = useMemo<LocationContext>(() => {
  if (routeLocationOverride) return routeLocationOverride
  return computeLocation({
    location,
    learningPathId,
    moduleId,
    quizId,
    quizAttemptId,
  })
}, [routeLocationOverride, location, learningPathId, moduleId, quizId, quizAttemptId])


  const onResizeStart = (e: React.MouseEvent) => {
    e.preventDefault()
    isResizingRef.current = true
    startMousePosRef.current = { x: e.clientX, y: e.clientY }
    startSizeRef.current = { ...size }

    document.body.style.userSelect = "none"
    document.body.style.cursor = "nw-resize"
    window.addEventListener("mousemove", onResizing)
    window.addEventListener("mouseup", onResizeEnd)
  }

  const onResizing = (e: MouseEvent) => {
  if (!isResizingRef.current) return
  const dx = startMousePosRef.current.x - e.clientX // tragere spre stânga => crește dx
  const dy = startMousePosRef.current.y - e.clientY // tragere în sus => crește dy

  const maxW = Math.min(window.innerWidth * 0.95, 900)
  const maxH = Math.min(window.innerHeight * 0.9, 900)

  const newWidth = Math.max(320, Math.min(startSizeRef.current.width + dx, maxW))
  const newHeight = Math.max(420, Math.min(startSizeRef.current.height + dy, maxH))
    setSize({ width: newWidth, height: newHeight })
  }

  const onResizeEnd = () => {
    isResizingRef.current = false
    document.body.style.userSelect = ""
    document.body.style.cursor = ""
    window.removeEventListener("mousemove", onResizing)
    window.removeEventListener("mouseup", onResizeEnd)
  }

  useOnClickOutside(wrapperRef, () => {})

  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    if (!userHasScrolledUp) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, userHasScrolledUp])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  const generateMessageId = () =>
    `msg_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`

  const addMessage = useCallback(
    (content: string, isUser: boolean, isStreaming = false): string => {
      const messageId = generateMessageId()
      const newMessage: ChatMessage = {
        id: messageId,
        content,
        isUser,
        timestamp: new Date(),
        isStreaming,
      }
      setMessages((prev) => [...prev, newMessage])
      return messageId
    },
    [],
  )

  const updateMessage = useCallback(
    (messageId: string, content: string, isStreaming = false) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, content, isStreaming } : msg,
        ),
      )
    },
    [],
  )

  const handleSendMessage = async () => {
    if (isLoading) return;

    // Check if input is empty
    if (!inputValue.trim()) {
      setInputError("Please type a message to send.")

      setTimeout(() => setInputError(null), 2500)
      return
    }

    const userMessage = inputValue.trim()
    setInputValue("")
    setIsLoading(true)
    setStatusMessage("")
    setInputError(null)

    addMessage(userMessage, true)
    const botMessageId = addMessage("", false, true)
    setStreamingMessageId(botMessageId)

    try {
      const chatRequest: ChatRequest = {
        user_id: userId,
        question: userMessage,
        location: computedLocation,
        learning_path_id: learningPathId,
        module_id: moduleId,
        quiz_id: quizId,
        quiz_attempt_id: quizAttemptId,
        team_id: teamId,
      }

      let accumulatedContent = ""
      for await (const message of chatApi.chatWithStream(chatRequest)) {
        switch (message.type) {
          case "connected":
            setStatusMessage("Connected to chat service...")
            break
          case "status":
            if (message.data?.message) {
              setStatusMessage(message.data.message)
            }
            break
          case "content":
            if (message.data?.content) {
              accumulatedContent += message.data.content
              updateMessage(botMessageId, accumulatedContent, true)
            }
            break
          case "metadata":
            // Treat metadata as end of stream
            if (accumulatedContent) {
              updateMessage(botMessageId, accumulatedContent, false)
            }
            setStatusMessage("")
            break
          case "complete":
            if (message.data?.final_result?.response) {
              updateMessage(botMessageId, message.data.final_result.response, false)
            } else if (accumulatedContent) {
              updateMessage(botMessageId, accumulatedContent, false)
            }
            setStatusMessage("")
            break
          case "error":
            const errorMessage = message.data?.message || "An error occurred while processing your request."
            updateMessage(botMessageId, `❌ ${errorMessage}`, false)
            setStatusMessage("")
            break
        }
      }
    } catch (error) {
      updateMessage(
        botMessageId,
        "❌ Sorry, I encountered an error while processing your request. Please try again.",
        false,
      )
      setStatusMessage("")
    } finally {
      setIsLoading(false)
      setStreamingMessageId(null)
    }
  }
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 10
    setUserHasScrolledUp(!isAtBottom)
    setShowScrollButton(!isAtBottom)
  }

  const scrollToBottom = (behavior: 'auto' | 'smooth' = 'auto') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScrollToBottom = () => {
    scrollToBottom('auto'); // Always use instant scroll for button clicks
  };

  const toggleChat = () => {
    setIsOpen(!isOpen)
    if (!isOpen) {
      setIsMinimized(false)
    }
  }
  const getLocationDisplayName = (loc: string) => {
    const locationMap: Record<string, string> = {
      dashboard: "Dashboard",
      learning_path: "Learning Path",
      module: "Module",
      quiz: "Quiz",
      quiz_attempt_active: "Active Quiz",
      review_answers: "Answer Review",
    }
    return locationMap[loc] || loc.charAt(0).toUpperCase() + loc.slice(1)
  }

  return (
    <div ref={wrapperRef} className={`fixed z-50 ${className}`}>
      <AnimatePresence>
      {!isOpen && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{
            type: "spring",
            stiffness: 400,
            damping: 25,
            duration: 0.3,
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleChat}
          className="fixed bottom-6 right-6 w-14 h-14  bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 hover:from-blue-700 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl flex items-center justify-center transition-shadow duration-200 border border-white/10"
        >
          <motion.div whileHover={{ rotate: 5 }} transition={{ type: "spring", stiffness: 300 }}>
            <MessageCircle className="w-6 h-6" />
          </motion.div>
        </motion.button>
      )}
    </AnimatePresence>

      {/* Chat window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed bottom-6 right-6 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/10 border border-white/20 flex flex-col overflow-hidden origin-bottom-right"
            style={{
              width: size.width,
              height: isMinimized ? "auto" : size.height,
            }}
          >
            <div
              onMouseDown={onResizeStart}
              title="Resize"
              className="absolute top-1 left-1 w-4 h-4 cursor-nw-resize z-20"
              style={{
                background:
                  "linear-gradient(315deg, transparent 0 40%, rgba(255,255,255,0.85) 45% 55%, transparent 60% 100%)",
              }}
            />

            {/* Header */}
            <div className="bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-700 text-white p-5 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent" />

              <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center gap-3">
                  {/* Resize handle */}

                  <div className="relative">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <Bot className="w-5 h-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-bold text-base flex items-center gap-2">
                      Learning Assistant
                      <Sparkles className="w-4 h-4 text-yellow-300" />
                    </h3>
                    <p className="text-xs text-white/80 font-medium">
                      Context: {getLocationDisplayName(computedLocation)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={toggleChat}
                    className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center transition-colors backdrop-blur-sm"
                  >
                    <X className="w-4 h-4" />
                  </motion.button>
                </div>
              </div>

              {/* Loading bar */}
              {isLoading && (
                <div className="mt-3 relative z-10">
                  <div className="w-full bg-white/20 rounded-full h-1.5 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                      style={{ width: "40%" }}
                      initial={{ x: "-100%" }}
                      animate={{ x: "250%" }}
                      transition={{ repeat: Infinity, repeatType: "loop", duration: 1.5, ease: "linear" }}
                    />
                  </div>
                  {statusMessage && (
                    <p className="text-xs text-white/80 mt-1">
                      {statusMessage}
                    </p>
                  )}
                </div>
              )}
            </div>


            {/* Chat content */}
            {!isMinimized && (
              <div className="flex flex-col flex-1 min-h-0 relative">
                <div
                  ref={scrollContainerRef}
                  onScroll={handleScroll}
                  className="flex-1 overflow-y-auto p-5 space-y-4 bg-gradient-to-b from-gray-50/50 to-white/50"
                  style={{
                    scrollBehavior: 'auto',
                    overscrollBehavior: 'contain', // Prevent scroll chaining
                  }}
                >
                  {messages.length === 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center text-gray-500 mt-12"
                    >
                      <div className="w-16 h-16 bg-gradient-to-br from-violet-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <Bot className="w-8 h-8 text-violet-600" />
                      </div>
                      <h4 className="font-semibold text-neutral-dark mb-2">
                        Welcome to your Learning Assistant!
                      </h4>
                      <p className="text-sm text-neutral-dark max-w-xs mx-auto leading-relaxed">
                        I'm here to help you with your learning journey. Ask me
                        anything about your progress, modules, or learning path!
                      </p>
                    </motion.div>
                  )}

                  {messages.map((message, index) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className={`flex ${
                        message.isUser ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 relative ${
                          message.isUser
                            ? "bg-gradient-to-br from-violet-600 to-purple-700 text-white shadow-lg shadow-violet-500/25"
                            : "bg-white text-gray-800 shadow-lg shadow-gray-500/10 border border-gray-100"
                        }`}
                      >
                        {!message.isUser && (
                          <div className="absolute -left-2 top-3 w-4 h-4 bg-white border border-gray-100 rotate-45 shadow-sm" />
                        )}
                        {message.isUser && (
                          <div className="absolute -right-1 top-3 w-4 h-4 bg-gradient-to-br from-violet-600 to-purple-700 rotate-45" />
                        )}

                        <div className="flex items-start space-x-3">
                          {!message.isUser && (
                            <div className="w-6 h-6 bg-gradient-to-br from-violet-100 to-purple-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Bot className="w-3.5 h-3.5 text-violet-600" />
                            </div>
                          )}
                          {message.isUser && (
                            <div className="w-6 h-6 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                              <User className="w-3.5 h-3.5 text-white" />
                            </div>
                          )}
                          <div className="flex-1">
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">
                              {renderFormattedText(message.content.trim())}
                            </p>
                            {message.isStreaming && (
                              <div className="flex items-center mt-2">
                                <Loader2 className="w-4 h-4 animate-spin text-violet-600" />
                                <span className="text-xs text-gray-500 ml-2">
                                  Thinking...
                                </span>
                              </div>
                            )}
                            <p className="text-xs opacity-60 mt-2">
                              {message.timestamp.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                {/* Scroll-down button */}
                <AnimatePresence>
                  {showScrollButton && (
                    <motion.button
                      onClick={handleScrollToBottom}
                      className="mb-2 px-3 py-2 bg-violet-600 text-white text-sm rounded-lg hover:bg-violet-700 transition-colors flex items-center space-x-2 shadow-lg"
                    >
                      <ArrowDown className="w-4 h-4" />
                      <span>Newer messages</span>
                    </motion.button>
                  )}
                </AnimatePresence>

                {/* Input text field */}
                <div className="border-t border-gray-100">
                  <AnimatePresence>
                    {inputError && (
                      <motion.div
                        initial={{ opacity: 0, height: 0, marginBottom: "0px" }}
                        animate={{ opacity: 1, height: "auto", marginBottom: "0px" }}
                        exit={{ opacity: 0, height: 0, marginBottom: "0px" }}
                        transition={{ duration: 0.2 }}
                        className="flex items-center text-sm text-red-600 space-x-2 font-medium pl-3"
                      >
                        <AlertTriangle className="w-4 h-4" />
                        <span>{inputError}</span>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="flex space-x-3 items-start px-2 pb-2 pt-2">
                    <div className="flex-1 relative">
                      <textarea
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => {
                          setInputValue(e.target.value)
                          if (inputError) {
                            setInputError(null)
                          }
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                        placeholder="Ask me anything..."
                        disabled={isLoading}
                        rows={1}
                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent text-sm disabled:opacity-50 transition-all duration-200 placeholder-gray-400 resize-none overflow-hidden min-h-[48px] max-h-[120px]"
                        style={{ height: 'auto' }}
                        onInput={(e) => {
                          const target = e.target as HTMLTextAreaElement;
                          target.style.height = 'auto';
                          const scrollHeight = Math.min(target.scrollHeight, 120);
                          target.style.height = `${scrollHeight}px`;
                        }}
                      />
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleSendMessage}
                      className="w-12 h-12 bg-gradient-to-br from-violet-600 to-purple-700 text-white rounded-xl hover:from-violet-700 hover:to-purple-800 transition-all duration-200 flex items-center justify-center shadow-lg shadow-violet-500/25 flex-shrink-0"
                    >
                      {isLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </motion.button>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
