import { motion } from "framer-motion"
import { Home, Compass, Sparkles } from "lucide-react"
import Link from "next/link"

export default function Custom404() {
  const fadeSlide = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: "easeOut" },
    },
  } as const

  const spring = {
    type: "spring",
    stiffness: 300,
    damping: 25,
  } as const

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        {Array.from({ length: 25 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-blue-300/20 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -25, 0],
              opacity: [0.2, 0.7, 0.2],
              scale: [1, 1.8, 1],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      <motion.div
        className="max-w-md w-full text-center relative z-10"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.2 } },
        }}
      >
        {/* 404 Icon with Animation */}
        <motion.div
          className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-full mb-8 relative"
          variants={fadeSlide}
          whileHover={{ scale: 1.1 }}
          transition={spring}
        >
          <div className="text-center">
            <div className="text-3xl font-bold">404</div>
            <Compass className="w-8 h-8 mx-auto mt-1" />
          </div>
          <motion.div
            className="absolute inset-0 rounded-full bg-blue-500"
            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2.5, repeat: Number.POSITIVE_INFINITY }}
          />
        </motion.div>

        {/* Error Title */}
        <motion.h1 className="text-4xl font-bold text-gray-800 mb-4" variants={fadeSlide}>
          Page Not Found
        </motion.h1>

        {/* Error Description */}
        <motion.p className="text-gray-600 mb-8 leading-relaxed" variants={fadeSlide}>
          The page you're looking for seems to have wandered off into the digital wilderness. Let's help you find your
          way back to your learning journey!
        </motion.p>

        {/* Action Buttons */}
        <motion.div className="space-y-4" variants={fadeSlide}>
          <Link href="/dashboard">
            <motion.button
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center space-x-2"
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              transition={spring}
            >
              <Home className="w-5 h-5" />
              <span>Go to Dashboard</span>
            </motion.button>
          </Link>

        </motion.div>

        {/* Fun Element */}
        <motion.div
          className="mt-8 p-4 bg-gradient-to-r from-purple-100 to-pink-100 border border-purple-200 rounded-lg"
          variants={fadeSlide}
        >
          <div className="flex items-center justify-center mb-2">
            <Sparkles className="w-4 h-4 text-purple-500 mr-2" />
            <span className="text-sm font-semibold text-purple-700">Fun Fact</span>
          </div>
          <p className="text-xs text-purple-600">
            Every wrong turn is just another step in your learning adventure! Even 404 errors teach us something new.
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}
