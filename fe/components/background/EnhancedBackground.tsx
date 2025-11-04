import { motion } from "framer-motion";

export default function EnhancedBackground()  {
    return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Main gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20"/>

        {/* Animated mesh gradient */}
        <div className="absolute inset-0">
            <motion.div
                className="absolute inset-0 opacity-40"
                animate={{
                    background: [
                        "radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(147, 51, 234, 0.05) 0%, transparent 50%), radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.03) 0%, transparent 50%)",
                        "radial-gradient(circle at 30% 40%, rgba(59, 130, 246, 0.06) 0%, transparent 50%), radial-gradient(circle at 70% 30%, rgba(147, 51, 234, 0.04) 0%, transparent 50%), radial-gradient(circle at 50% 70%, rgba(236, 72, 153, 0.04) 0%, transparent 50%)",
                        "radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(147, 51, 234, 0.05) 0%, transparent 50%), radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.03) 0%, transparent 50%)"
                    ]
                }}
                transition={{duration: 20, repeat: Infinity, ease: "easeInOut"}}
            />
        </div>

        {/* Grid pattern */}
        <div
            className="absolute inset-0 opacity-[0.015]"
            style={{
                backgroundImage: `
          linear-gradient(rgba(59, 130, 246, 0.3) 1px, transparent 1px),
          linear-gradient(90deg, rgba(59, 130, 246, 0.3) 1px, transparent 1px)
        `,
                backgroundSize: "60px 60px",
            }}
        />

        {/* Floating orbs */}
        <motion.div
            className="absolute top-20 right-16 w-72 h-72 rounded-full"
            style={{
                background: "conic-gradient(from 0deg at 50% 50%, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.06), rgba(236, 72, 153, 0.04), rgba(59, 130, 246, 0.08))"
            }}
            animate={{
                y: [0, -30, 0],
                x: [0, 20, 0],
                rotate: [0, 180, 360],
                scale: [1, 1.1, 1],
            }}
            transition={{
                duration: 25,
                repeat: Infinity,
                ease: "easeInOut",
                times: [0, 0.5, 1]
            }}
        />

        <motion.div
            className="absolute bottom-32 left-16 w-56 h-56 rounded-full"
            style={{
                background: "conic-gradient(from 180deg at 50% 50%, rgba(16, 185, 129, 0.06), rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.05), rgba(16, 185, 129, 0.06))"
            }}
            animate={{
                y: [0, 25, 0],
                x: [0, -25, 0],
                rotate: [360, 180, 0],
                scale: [1, 1.15, 1],
            }}
            transition={{
                duration: 20,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 3
            }}
        />

        <motion.div
            className="absolute top-1/3 left-1/4 w-32 h-32 rounded-full"
            style={{
                background: "radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, rgba(249, 115, 22, 0.04) 50%, transparent 100%)"
            }}
            animate={{
                y: [0, -15, 0],
                x: [0, 15, 0],
                scale: [1, 1.2, 1],
                opacity: [0.8, 0.4, 0.8]
            }}
            transition={{
                duration: 15,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1
            }}
        />

        <motion.div
            className="absolute top-2/3 right-1/3 w-24 h-24 rounded-full"
            style={{
                background: "radial-gradient(circle, rgba(236, 72, 153, 0.1) 0%, rgba(219, 39, 119, 0.05) 50%, transparent 100%)"
            }}
            animate={{
                rotate: [0, 360],
                scale: [1, 1.3, 1],
                opacity: [0.6, 1, 0.6]
            }}
            transition={{
                duration: 18,
                repeat: Infinity,
                ease: "linear"
            }}
        />

        {/* Animated particles */}
        {[...Array(8)].map((_, i) => (
            <motion.div
                key={i}
                className="absolute w-2 h-2 rounded-full bg-gradient-to-r from-blue-400/20 to-purple-400/20"
                style={{
                    left: `${10 + (i * 12)}%`,
                    top: `${20 + (i * 8)}%`,
                }}
                animate={{
                    y: [0, -100, 0],
                    opacity: [0, 1, 0],
                    scale: [0.5, 1.5, 0.5],
                }}
                transition={{
                    duration: 4 + (i * 0.5),
                    repeat: Infinity,
                    delay: i * 0.8,
                    ease: "easeInOut"
                }}
            />
        ))}

        {/* Subtle noise texture overlay */}
        <div
            className="absolute inset-0 opacity-[0.015] mix-blend-overlay"
            style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
            }}
        />

        {/* Radial overlay */}
        <div className="absolute inset-0 bg-gradient-radial from-transparent via-white/5 to-slate-100/20"/>

        {/* Top fade */}
        <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-white/10 to-transparent"/>
    </div>
    )
}