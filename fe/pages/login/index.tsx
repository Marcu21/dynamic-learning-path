"use client"

import type React from "react"
import { useState, useEffect } from "react"
import Image from "next/image"
import { useRouter } from "next/router"
import { motion, AnimatePresence } from "framer-motion"
import { User, Brain, Sparkles, Mail, CheckCircle, AlertCircle, X, AlertTriangle } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import ParticlesBackground from "@/components/background/ParticlesBackground"
import { api } from "@/lib/api"
import * as anim from "@/components/auth/login/animations"
import * as styles from "@/components/auth/login/styles"
import { fadeSlide, spring } from "@/components/auth/login/animations"

type Dot = { x: number; y: number; duration: number; delay: number }

interface FormState {
  isLoading: boolean
  message: string
  messageType: "success" | "error" | "warning" | "info" | ""
}

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const router = useRouter()
  const [emailInput, setEmailInput] = useState("")
  const [isVerifyingToken, setIsVerifyingToken] = useState(true)
  const [dots, setDots] = useState<Dot[]>([])
  const [formState, setFormState] = useState<FormState>({
    isLoading: false,
    message: "",
    messageType: "",
  })
  const [emailError, setEmailError] = useState<string>("")

  useEffect(() => {
    setDots(
      Array.from({ length: 8 }).map(() => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
        duration: 3 + Math.random() * 2,
        delay: Math.random() * 3,
      })),
    )
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard")
      return
    }

    if (!router.isReady) {
      return
    }

    const { token } = router.query

    if (token && typeof token === "string") {
      const handleTokenLogin = async (tokenValue: string) => {
        try {
          await login(tokenValue)
          router.push("/dashboard")
        } catch (error) {
          setFormState({
            isLoading: false,
            message: "Login failed. The link may have expired or is invalid. Please try again.",
            messageType: "error",
          })
          router.replace("/login", undefined, { shallow: true })
          setIsVerifyingToken(false)
        }
      }

      handleTokenLogin(token)
    } else {
      setIsVerifyingToken(false)
    }
  }, [isAuthenticated, router, login])

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (formState.isLoading) {
      return
    }

    dismissMessage();

    if (!validateEmail(emailInput)) {
      setEmailError("Please enter a valid email address.")
      return
    }

    setEmailError("")

    setFormState({ isLoading: true, message: "", messageType: "" })

    try {
      await api.sendMagicLink(emailInput)
      setFormState({
        isLoading: false,
        message: "Magic link sent! Check your email for the login link.",
        messageType: "success",
      })
      setEmailInput("")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred. Please try again."

      setFormState({
        isLoading: false,
        message: errorMessage,
        messageType: "error",
      })
    }
  }

  const dismissMessage = () => {
    setFormState((prev) => ({ ...prev, message: "", messageType: "" }))
  }
  const featureColors = [
    { bg: "bg-purple-100", text: "text-purple-600", Icon: Brain, label: "AI-Powered" },
    { bg: "bg-pink-100", text: "text-pink-600", Icon: User, label: "Personalized" },
    { bg: "bg-blue-100", text: "text-blue-600", Icon: Sparkles, label: "Interactive" },
  ]

  if (isVerifyingToken || isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <ParticlesBackground />
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-lg text-gray-600 font-sans">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className={styles.wrapper}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.2 } },
      }}
    >
      <ParticlesBackground />

      <motion.div
        className="absolute top-20 left-20 w-16 h-16 bg-primary/20 rounded-full blur-xl"
        variants={anim.floatAnimation}
        animate="animate"
      />
      <motion.div
        className="absolute top-40 right-32 w-24 h-24 bg-accent/20 rounded-full blur-xl"
        variants={anim.floatAnimation}
        animate="animate"
        transition={{ delay: 1 }}
      />
      <motion.div
        className="absolute bottom-32 left-40 w-20 h-20 bg-success/20 rounded-full blur-xl"
        variants={anim.floatAnimation}
        animate="animate"
        transition={{ delay: 2 }}
      />

      <motion.div className={styles.cardContainer} variants={anim.fadeSlide}>
        <motion.div className={styles.cardBase}>
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-primary/5 via-accent/5 to-success/5 opacity-50"
            animate={{ backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"] }}
            transition={{ duration: 10, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            style={{ backgroundSize: "200% 200%" }}
          />

          <div className="absolute inset-0 overflow-hidden rounded-2xl">
            {dots.map((p, i) => (
              <motion.div
                key={i}
                className="absolute w-1 h-1 bg-primary/40 rounded-full"
                style={{ left: `${p.x}%`, top: `${p.y}%` }}
                animate={{ y: [0, -20, 0], opacity: [0.2, 0.8, 0.2], scale: [1, 1.5, 1] }}
                transition={{
                  duration: p.duration,
                  repeat: Number.POSITIVE_INFINITY,
                  ease: "easeInOut",
                  delay: p.delay,
                }}
              />
            ))}
          </div>

          <div className="relative z-10">
            <motion.div className="text-center mb-8" variants={anim.fadeSlide}>
              <motion.div
                className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-4"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 4, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              >
                <Image
                  src="/logo.png"
                  alt="Site Logo"
                  width={42}
                  height={30}
                  priority
                  style={{
                    width: '42px',
                    height: 'auto',
                    maxWidth: '42px',
                    maxHeight: '30px'
                  }}
                />
                <motion.div
                  className="absolute inset-0 rounded-full bg-primary"
                  animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
                  transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY }}
                />
              </motion.div>

              <motion.h1
                className="text-2xl font-display font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent"
                style={{ backgroundSize: "200% 100%" }}
              >
                Skill Central
              </motion.h1>

              <motion.div
                className="text-base text-neutral-dark py-2 font-sans flex items-center justify-center"
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY }}
              >
                <Sparkles className="w-4 h-4 text-accent mr-2" />
                <span>Your personalized learning journey starts here</span>
              </motion.div>
            </motion.div>

            <motion.form onSubmit={handleSubmit} className="space-y-4" variants={anim.fadeSlide}>
              <div className="space-y-1">
                <label htmlFor="email" className="block text-md font-sans font-bold text-neutral-dark">
                  Email Address
                </label>
                <div className="relative">
                  <motion.input
                    id="email"
                    type="email"
                    value={emailInput}
                    onChange={(e) => {
                      setEmailInput(e.target.value)
                      if (emailError) setEmailError("")
                    }}
                    placeholder="Enter your email"
                    className={`${styles.inputBase} text-md placeholder:text-md placeholder:text-neutral-secondary-light ${
                      emailError 
                        ? "!border-red-500 ring-1 !ring-red-500" 
                        : "focus:ring-purple-500"
                    }`}
                    whileFocus={{ scale: 1.02 }}
                    transition={anim.spring}
                  />
                  <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-neutral-secondary-light" />
                </div>
                <AnimatePresence>
                  {emailError && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      transition={{ duration: 0.2 }}
                      className="flex items-center text-sm text-red-600 space-x-1.5 pt-1"
                    >
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{emailError}</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <motion.div whileTap={{ scale: 0.98 }} transition={spring} className="pt-2">
                <button
                  type="submit"
                  className="w-full flex items-center justify-center space-x-2 text-white text-md font-semibold py-3 px-4 rounded-xl shadow-lg transition-all duration-500 transform hover:scale-105 bg-gradient-to-r from-purple-600 via-pink-500 to-blue-500"
                  style={{ backgroundSize: "200% auto" }}
                  onMouseOver={(e) => (e.currentTarget.style.backgroundPosition = "right center")}
                  onMouseOut={(e) => (e.currentTarget.style.backgroundPosition = "left center")}
                >
                  {formState.isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Sending Magic Link...</span>
                    </>
                  ) : (
                    <span>Send Magic Link</span>
                  )}
                </button>
              </motion.div>

              <AnimatePresence>
                {formState.message && (
                  <motion.div
                    key="message"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    transition={{ duration: 0.2 }}
                    className={`p-4 rounded-xl flex items-center space-x-3 ${
                      formState.messageType === "success"
                        ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                        : formState.messageType === "warning"
                          ? "bg-amber-50 border border-amber-200 text-amber-800"
                          : "bg-red-50 border border-red-200 text-red-800"
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {formState.messageType === "success" ? (
                        <div className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                          <CheckCircle className="w-4 h-4 text-white" />
                        </div>
                      ) : formState.messageType === "warning" ? (
                        <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center">
                          <AlertTriangle className="w-4 h-4 text-white" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                          <AlertCircle className="w-4 h-4 text-white" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1">
                      <p className="text-md font-medium">{formState.message}</p>
                    </div>

                    <button
                      type="button"
                      onClick={dismissMessage}
                      className="flex-shrink-0 p-1 rounded-full hover:bg-white/50 transition-colors duration-200"
                    >
                      <X className="w-4 h-4 opacity-60 hover:opacity-100" />
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              <motion.div className="mt-8 pt-6 border-t border-gray-200" variants={fadeSlide}>
                <div className="grid grid-cols-3 gap-4 text-center">
                  {featureColors.map(({ Icon, label, bg, text }, i) => (
                    <motion.div
                      key={label}
                      className="space-y-2 flex flex-col items-center"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 + i * 0.1 }}
                      whileHover={{ scale: 1.05, y: -3 }}
                    >
                      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${bg}`}>
                        <Icon className={`w-5 h-5 ${text}`} />
                      </div>
                      <p className="text-sm font-sans text-neutral-dark">{label}</p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </motion.form>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  )
}