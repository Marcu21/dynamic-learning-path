import React, { useState, useEffect, JSX } from 'react';
import Image from "next/image";
import { motion, AnimatePresence, Variants } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  Users,
  Target,
  Brain,
  Info,
  X,
  Clock,
  TrendingUp,
  Zap,
  Filter,
  BarChart3,
  Layers,
  CheckCircle,
  ArrowRight,
  Database,
  Server,
  Globe,
  Cpu,
  Award,
  Rocket,
  BookOpen,
  FileText, Video,
  Code
} from 'lucide-react';
import Link from "next/link";

// Brand Colors
export const CC = {
  navy: '#203878',
  blue: '#134B8E',
  cyan: '#0098D8',
  fog: 'rgba(255, 255, 255, 0.1)',
  white: '#ffffff'
};

const FallingIconsBackground = () => {
  const icons = [BookOpen, FileText, Video, Code, Brain];
  const items = Array.from({ length: 30 }, (_, i) => {
    const Icon = icons[i % icons.length];
    const duration = Math.random() * 10 + 8; // Calculate duration once
    return {
      id: i,
      Icon,
      x: Math.random() * 100,
      size: Math.random() * 24 + 16, // size between 16px and 40px
      duration: duration,
      delay: Math.random() * -duration,
    };
  });

  return (
    <div className="absolute inset-0 w-full h-full pointer-events-none z-0">
      {items.map((item) => (
        <motion.div
          key={item.id}
          className="absolute text-white/10"
          style={{
            left: `${item.x}%`,
            top: '-10%',
            width: item.size,
            height: item.size,
          }}
          animate={{
            y: '120vh',
          }}
          transition={{
            duration: item.duration,
            delay: item.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <item.Icon className="w-full h-full" />
        </motion.div>
      ))}
    </div>
  );
};


// Animation variants with proper typing
const containerV: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1
    }
  }
};

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 40 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 120,
      damping: 20
    }
  }
};

const cardV: Variants = {
  hidden: { opacity: 0, y: 30, scale: 0.9 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 150,
      damping: 25,
      delay: i * 0.1
    }
  })
};

// Particles Background Component
const ParticlesBackground = () => {
  const particles = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 4 + 1,
    duration: Math.random() * 20 + 10,
  }));

  return (
    <div className="fixed inset-0 pointer-events-none">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute bg-white/20 rounded-full"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: particle.size,
            height: particle.size,
          }}
          animate={{
            y: [0, -100, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
};

interface ModalContent {
  title: string;
  content: React.ReactNode;
}

interface Slide {
  id: number;
  title: string;
  bgColor: string;
  textColor: string;
  content: React.ReactNode;
}

const SkillCentralPresentation: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState<number>(0);
  const [showModal, setShowModal] = useState<boolean>(false);
  const [modalContent, setModalContent] = useState<ModalContent | null>(null);

  const manualSteps = [
    {
      step: 1,
      title: "Platform Hunting",
      desc: "Endlessly browse multiple platforms like YouTube, Spotify, and academic sites.",
    },
    {
      step: 2,
      title: "Content Vetting",
      desc: "Skim titles, read descriptions, and sample content for 10-60s just to shortlist.",
    },
    {
      step: 3,
      title: "Manual Organization",
      desc: "Manually order modules; save links across notes, docs, or spreadsheets.",
    },
    {
      step: 4,
      title: "Constant Maintenance",
      desc: "Maintain versions, reshuffle as you learn, and track all your progress by hand.",
    }
  ];
// Replace your existing ImplementationSlideContent component with this one.
const ImplementationSlideContent = () => {
  const [hoveredModule, setHoveredModule] = useState<{
    icon: JSX.Element;
    title: string;
    desc: string;
    x: number;
    y: number;
    angle: number;
  } | null>(null);

  const modules = [
    { icon: <CheckCircle className="w-8 h-8"/>, title: "Quizzing", desc: "Generates tests to verify knowledge." },
        { icon: <Award className="w-8 h-8"/>, title: "Profiles", desc: "Showcases skills and certificates." },
    { icon: <Users className="w-8 h-8"/>, title: "Team Analytics", desc: "Provides insights for team leaders." },
        { icon: <BarChart3 className="w-8 h-8"/>, title: "Tracking", desc: "Monitors your learning progress." },

    { icon: <Database className="w-8 h-8"/>, title: "Aggregation", desc: "Gathers content from multiple sources." },
    { icon: <TrendingUp className="w-8 h-8"/>, title: "Ranking", desc: "Sorts content by relevance and quality." },

  ];

  // Banner component with updated size and distance
  const Banner = ({ title, desc, icon, x, y, angle }: { title: string, desc: string, icon: JSX.Element, x: number, y: number, angle: number }) => {
    let bannerStyle: {};
    let tailStyle: {};
    const bannerWidth = 384;

    const isLeftSide = angle >= (Math.PI / 2) && angle < (3 * Math.PI / 2);

    if (isLeftSide) {
      // Open banner to the LEFT
      bannerStyle = {
        top: y + 100 ,
        left: x - 250,
        transform: `translateX(-${bannerWidth}px) translateY(-50%)`
      };
      tailStyle = { top: "50%", right: 0, transform: "translate(50%, -50%) rotate(135deg)" };
    } else {
      // Open banner to the RIGHT
      bannerStyle = {
        top: y + 100,
        left: x + 250 ,
        transform: "translateY(-50%)"
      };
      tailStyle = { top: "50%", left: 0, transform: "translate(-50%, -50%) rotate(-45deg)" };
    }

    return (
      <motion.div
        className="absolute w-96 p-6 bg-white/10 backdrop-blur-xl rounded-lg border border-white/20 shadow-xl z-20"
        style={bannerStyle}
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.85 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        <div className="absolute w-5 h-5 bg-white/10 border-t border-l border-white/20" style={tailStyle} />
        <div className="flex items-center mb-3">
          {React.cloneElement(icon, { className: "w-9 h-9 mr-5 text-cyan-300 flex-shrink-0"})}
          <h3 className="text-2xl font-bold text-white">{title}</h3>
        </div>
        <p className="text-lg text-white/80 leading-relaxed pl-[56px]">{desc}</p>
      </motion.div>
    );
  };

  return (
    <motion.div
      className="space-y-12"
      variants={containerV}
      initial="hidden"
      animate="show"
    >
      <motion.h1 variants={fadeUp} className="text-6xl font-bold text-center mb-16">
        Our <span className="text-cyan-300">Solution</span>
      </motion.h1>

      <motion.div className="w-full flex items-center justify-center min-h-[500px]">
        <div className="relative w-96 h-96 flex items-center justify-center">
          <motion.div className="absolute flex flex-col items-center justify-center bg-cyan-500/20 rounded-full w-48 h-48 border-2 border-cyan-400 shadow-[0_0_30px_rgba(0,152,216,0.5)]">
            <Image src="/logo.png" alt="Skill Central Logo" width={70} height={70} priority />
            <h3 className="text-xl font-bold my-2">Skill Central</h3>
          </motion.div>

          {modules.map((module, i) => {
            const angle = (i / modules.length) * 2 * Math.PI;
            const radius = 220;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            return (
              <motion.div
                key={module.title}
                className="absolute"
                onHoverStart={() => setHoveredModule({ ...module, x, y, angle })}
                initial={{ opacity: 0, scale: 0, x: 0, y: 0 }}
                animate={{
                  opacity: 1,
                  scale: hoveredModule?.title === module.title ? 1.15 : 1,
                  x,
                  y,
                }}
                transition={{
                  type: "spring",
                  stiffness: 120,
                  damping: 15,
                  delay: 0.5 + i * 0.15,
                }}
              >
                <motion.div
                  className="flex flex-col items-center text-center w-36"
                  animate={{ y: [0, -6, 0] }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    repeatType: "mirror",
                    ease: "easeInOut",
                  }}
                >
                  <div className="flex items-center justify-center w-20 h-20 bg-white/10 backdrop-blur-lg rounded-full border border-white/20 mb-3 cursor-pointer">
                    {module.icon}
                  </div>
                  <h4 className="font-semibold text-lg">{module.title}</h4>
                </motion.div>
              </motion.div>
            );
          })}

          <AnimatePresence>
            {hoveredModule && <Banner {...hoveredModule} />}
          </AnimatePresence>
        </div>
      </motion.div>
    </motion.div>
  );
};

  const slides: Slide[] = [
    // Slide 1: Title
    {
      id: 0,
      title: "Skill Central",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: (
       <motion.div
         className="text-center space-y-8"
         variants={containerV}
         initial="hidden"
         animate="show"
       >
         <motion.div variants={fadeUp} className="flex justify-center mb-6">
           <motion.div
             animate={{
               rotate: [0, 5, -5, 0],
               scale: [1, 1.06, 1]
             }}
             transition={{
               duration: 4,
               repeat: Infinity,
               ease: "easeInOut"
             }}
           >
             <Image
              src="/logo.png"
              alt="Skill Central Logo"
              width={180}
              height={144}
              priority
              style={{
                width: 'auto',
                height: '144px',
                maxWidth: '180px',
                maxHeight: '180px'
              }}
              />
           </motion.div>
         </motion.div>

         <motion.h1
           variants={fadeUp}
           className="text-8xl md:text-8xl font-extrabold tracking-tight leading-tight drop-shadow-[0_4px_24px_rgba(0,152,216,0.35)]"
           transition={{ type: "spring", stiffness: 180 }}
         >
           Skill Central
         </motion.h1>

         <motion.p
           variants={fadeUp}
           className="text-3xl md:text-4xl font-semibold text-white/90 max-w-6xl mx-auto leading-tight"
         >
           Taking you to the{" "}
           <span className="relative inline-block whitespace-nowrap">
             <span className="bg-gradient-to-r from-cyan-300 via-sky-300 to-white bg-clip-text text-transparent">
               next level
             </span>
             <span className="absolute -bottom-1 left-0 right-0 h-0.5 rounded-full bg-gradient-to-r from-cyan-400/60 to-sky-400/60"/>
           </span>
         </motion.p>

         <motion.p
           variants={fadeUp}
           className="text-2xl md:text-3xl text-white/80 max-w-5xl mx-auto"
         >
           Both personally and in your career
         </motion.p>

         <motion.div
           className="grid md:grid-cols-3 gap-6 max-w-7xl mx-auto mt-8"
           variants={containerV}
         >
           {[
             { icon: <Target className="w-8 h-8"/>, title: "Personalized Paths" },
             { icon: <Brain className="w-8 h-8"/>, title: "AI-Powered" },
             { icon: <Users className="w-8 h-8"/>, title: "Team-ready" }
           ].map((item, i) => (
             <motion.div
               key={i}
               className="rounded-xl p-7 backdrop-blur-md bg-white/10 border-l-4 border-cyan-400"
               variants={cardV}
               custom={i}
               whileHover={{ y: -4 }}
             >
               <div className="flex items-center gap-3">
                 {item.icon}
                 <h4 className="text-2xl font-semibold">{item.title}</h4>
               </div>
             </motion.div>
           ))}
         </motion.div>
       </motion.div>
      )
    },

// Slide 2: The Problem - Abundance (UPDATED)
{
  id: 1,
  title: "The Problem",
  bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
  textColor: "text-white",
  content: (
    // Add position: relative here to contain the absolute positioned background
    <div className="relative">
      <FallingIconsBackground /> {/* Add the new component here */}
      <motion.div
        className="text-center space-y-16 relative z-10" // Add relative and z-10 to ensure content is on top
        variants={containerV}
        initial="hidden"
        animate="show"
      >
        <motion.h1
          variants={fadeUp}
          className="text-6xl font-bold mb-8"
        >
          The Problem: <span className="text-cyan-300">Abundance</span>
        </motion.h1>

        <motion.div
          className="grid md:grid-cols-2 gap-12 max-w-6xl mx-auto"
          variants={containerV}
        >
          <motion.div
            variants={cardV}
            className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
          >
            <Filter className="w-16 h-16 text-cyan-300 mx-auto mb-6" />
            <h3 className="text-3xl font-bold mb-4">Information Overload</h3>
            <p className="text-xl text-white/90">
              Millions of learning resources published every month → difficult to filter signal from noise
            </p>
          </motion.div>

          <motion.div
            variants={cardV}
            custom={1}
            className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
          >
            {/* Animated Clock Icon */}
            <motion.div
              className="w-16 h-16 text-cyan-300 mx-auto mb-6"
              animate={{ rotate: 360 }}
              transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
            >
              <Clock className="w-full h-full" />
            </motion.div>
            <h3 className="text-3xl font-bold mb-4">Time Crisis</h3>
            <p className="text-xl text-white/90">
              Even sampling 0.01% of a year's content at 10s/resource ≈ 2+ years of nonstop viewing
            </p>
          </motion.div>
        </motion.div>

        <motion.div
          variants={fadeUp}
          className="bg-gradient-to-r from-red-500/20 to-orange-500/20 backdrop-blur-lg rounded-xl p-6 max-w-4xl mx-auto border border-red-300/30"
        >
          <p className="text-2xl font-semibold text-white">
            💡 We're drowning in content, but starving for structured learning paths
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
},

    // Slide 3: SkillCentral at a Glance
    {
      id: 2,
      title: "Skill Central at a Glance",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: (
        <motion.div
          className="space-y-12"
          variants={containerV}
          initial="hidden"
          animate="show"
        >
          <motion.h1
            variants={fadeUp}
            className="text-6xl font-bold text-center mb-8"
          >
            Skill Central <span className="text-cyan-300">at a Glance</span>
          </motion.h1>

          <motion.div
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto"
            variants={containerV}
          >
            {[
              {
                icon: <Target className="w-12 h-12" />,
                title: "Personalized Learning Path",
                desc: "From your preferred learning style (visual / auditory / reading / practical)"
              },
              {
                icon: <Layers className="w-12 h-12" />,
                title: "Centralized Hub",
                desc: "Resources, progress, all in one place"
              },
              {
                icon: <Users className="w-12 h-12" />,
                title: "Team Mode",
                desc: "Shared paths, aggregated insights"
              },
              {
                icon: <CheckCircle className="w-12 h-12" />,
                title: "Quizzes & Points",
                desc: "Immediate feedback and gamification"
              },
              {
                icon: <Brain className="w-12 h-12" />,
                title: "AI Learning Assistant",
                desc: "Your learning copilot"
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                variants={cardV}
                custom={i}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-colors"
                whileHover={{ y: -8, scale: 1.02 }}
              >
                <div className="text-cyan-300 mb-4">{feature.icon}</div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-white/80">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )
    },

    {
      id: 3,
      title: "Manual Process",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: (
        <motion.div
          className="space-y-12"
          variants={containerV}
          initial="hidden"
          animate="show"
        >
          <motion.h1
            variants={fadeUp}
            className="text-6xl font-bold text-center mb-8"
          >
            Manual Process <span className="text-red-400">(Without Skill Central)</span>
          </motion.h1>

          {/* New 2x2 grid layout for the 4 cards */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto"
            variants={containerV}
          >
            {manualSteps.map((step, i) => (
            <motion.div
              key={i}
              // Use a modified variant for enter animation that DOES NOT control scale.
              variants={{
                hidden: { opacity: 0, y: 30 }, // Removed scale
                show: (i: number) => ({
                  opacity: 1,
                  y: 0,
                  transition: {
                    type: "spring",
                    stiffness: 150,
                    damping: 25,
                    delay: i * 0.1,
                  },
                }),
              }}
              custom={i}
              // The `animate` prop is now the sole driver of the continuous animation.
              animate={{
                scale: [1, 1.04, 1],
                boxShadow: [
                  "0 0 0 rgba(239, 68, 68, 0)",
                  "0 0 20px rgba(239, 68, 68, 0.7)",
                  "0 0 0 rgba(239, 68, 68, 0)",
                ],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                repeatType: "loop",
                repeatDelay: 9,
                delay: i * 2.8 + 0.5,
              }}
              className="flex flex-col items-center text-center gap-4 bg-red-500/10 backdrop-blur-lg rounded-xl p-8 border border-red-300/30"
            >
              <div className="flex items-center justify-center gap-4 w-full mb-4">
                <div className="flex-shrink-0 w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center text-2xl font-bold">
                  {step.step}
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold mb-2 text-red-300">{step.title}</h3>
                <p className="text-lg text-white/90">{step.desc}</p>
              </div>
            </motion.div>
          ))}
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="text-center bg-red-500/20 backdrop-blur-lg rounded-xl p-6 max-w-4xl mx-auto border border-red-300/30"
          >
            <p className="text-2xl font-semibold text-white">
              ⚠️ Time-consuming, error-prone, and frustrating
            </p>
          </motion.div>
        </motion.div>
      )
    },

    {
      id: 4,
      title: "Our Implementation",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: <ImplementationSlideContent />,
    },

    // Slide 6: Key Benefits
    {
     id: 5,
     title: "Key Benefits",
     bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
     textColor: "text-white",
     content: (
       <motion.div
         className="space-y-12"
         variants={containerV}
         initial="hidden"
         animate="show"
       >
         <motion.h1
           variants={fadeUp}
           className="text-6xl font-bold text-center mb-8"
         >
           Key <span className="text-cyan-300">Benefits</span>
         </motion.h1>

         <motion.div
           className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto"
           variants={containerV}
         >
           {[
             {
               icon: <Zap className="w-12 h-12" />,
               title: "Save Time & Stay Focused",
               desc: "Curated, sequenced content with clear next steps"
             },
             {
               icon: <TrendingUp className="w-12 h-12" />,
               title: "Boost Motivation",
               desc: "Quizzes, streaks, and shareable milestones"
             },
             {
               icon: <Users className="w-12 h-12" />,
               title: "Collaborate Effectively",
               desc: "Team paths and actionable analytics"
             },
             {
               icon: <Globe className="w-12 h-12" />,
               title: "Access Quality Sources",
               desc: "YouTube, Spotify, Google Books, Research Papers, Codeforces"
             }
           ].map((benefit, i) => (
             <motion.div
               key={i}
               variants={cardV}
               custom={i}
               className="bg-white/10 backdrop-blur-lg p-8 rounded-2xl border border-white/20 hover:border-cyan-300/40 transition-all duration-300"
               whileHover={{
                 y: -8,
                 scale: 1.02,
                 boxShadow: "0 20px 40px rgba(0, 152, 216, 0.15)",
                 transition: {
                   type: "spring",
                   stiffness: 300,
                   damping: 20
                 }
               }}
             >
               <motion.div
                 className="text-cyan-300 mb-6"
                 whileHover={{
                   rotate: 10,
                   scale: 1.1,
                   transition: {
                     type: "spring",
                     stiffness: 300,
                     damping: 15
                   }
                 }}
               >
                 {benefit.icon}
               </motion.div>
               <motion.h3
                 className="text-2xl font-bold text-white mb-4"
                 whileHover={{
                   x: 5,
                   transition: {
                     type: "spring",
                     stiffness: 300,
                     damping: 15
                   }
                 }}
               >
                 {benefit.title}
               </motion.h3>
               <p className="text-lg text-white/80">{benefit.desc}</p>
             </motion.div>
           ))}
         </motion.div>

         <motion.div
           variants={fadeUp}
           className="text-center bg-white/10 backdrop-blur-lg rounded-xl p-8 max-w-4xl mx-auto border border-white/20"
         >
           <motion.p
             className="text-2xl font-semibold text-white mb-4"
             animate={{
               scale: [1, 1.02, 1]
             }}
             transition={{
               duration: 3,
               repeat: Infinity,
               ease: [0.4, 0, 0.6, 1]
             }}
           >
             🚀 Transform scattered learning into structured success
           </motion.p>
         </motion.div>
       </motion.div>
     )
    },

    // Slide 7: How It Works - Steps
    {
       id: 6,
       title: "How It Works - Steps",
       bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
       textColor: "text-white",
       content: (
         <motion.div
           className="space-y-8 h-full flex flex-col justify-center"
           variants={containerV}
           initial="hidden"
           animate="show"
         >
           <motion.h1
             variants={fadeUp}
             className="text-5xl font-bold text-center mb-12"
           >
             How It <span className="text-cyan-300">Works</span>
           </motion.h1>

           <motion.div
             className="grid grid-cols-2 gap-6 max-w-6xl mx-auto"
             variants={containerV}
           >
             {[
               {
                 step: "01",
                 title: "User Input",
                 desc: "Share your learning goals, skill level, preferred platforms, and available time",
                 icon: <Target className="w-8 h-8" />
               },
               {
                 step: "02",
                 title: "Blueprint Creation",
                 desc: "Generate learning path title, module count, and difficulty progression",
                 icon: <Brain className="w-8 h-8" />
               },
               {
                 step: "03",
                 title: "Query Generation",
                 desc: "Create tailored search queries based on difficulty and learning objectives",
                 icon: <Zap className="w-8 h-8" />
               },
               {
                 step: "04",
                 title: "Content Pooling",
                 desc: "Aggregate quality content from all platforms using generated queries",
                 icon: <Database className="w-8 h-8" />
               },
               {
                 step: "05",
                 title: "Module Selection",
                 desc: "Select the best content for each module with clear objectives and difficulty",
                 icon: <CheckCircle className="w-8 h-8" />
               },
               {
                 step: "06",
                 title: "Path Complete",
                 desc: "Your personalized learning journey is ready with structured modules",
                 icon: <Rocket className="w-8 h-8" />
               }
             ].map((item, i) => (
               <motion.div
                 key={i}
                 variants={cardV}
                 custom={i}
                 className="bg-white/10 backdrop-blur-lg p-4 rounded-xl border border-white/20"
                 whileHover={{
                   scale: 1.02,
                   y: -4,
                   transition: {
                     type: "spring",
                     stiffness: 400,
                     damping: 25
                   }
                 }}
                 animate={{
                   y: [0, -2, 0]
                 }}
                 transition={{
                   y: {
                     duration: 4,
                     repeat: Infinity,
                     ease: [0.4, 0, 0.6, 1],
                     delay: i * 0.3
                   }
                 }}
               >
                 <div className="flex items-center gap-4 mb-4">
                   <div className="flex-shrink-0 w-16 h-16 bg-cyan-500/30 rounded-full flex items-center justify-center text-xl font-bold text-cyan-300">
                     {item.step}
                   </div>
                   <motion.div
                     className="text-cyan-300"
                     animate={{
                       rotate: [0, 2, -2, 0]
                     }}
                     transition={{
                       duration: 6,
                       repeat: Infinity,
                       ease: [0.4, 0, 0.6, 1],
                       delay: i * 0.2
                     }}
                   >
                     {item.icon}
                   </motion.div>
                 </div>
                 <h3 className="text-2xl font-bold text-white mb-3">{item.title}</h3>
                 <p className="text-white/80 text-lg leading-relaxed">{item.desc}</p>
               </motion.div>
             ))}
           </motion.div>
         </motion.div>
       )
      },

    {
     id: 8,
     title: "How It Works - Flow",
     bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
     textColor: "text-white",
     content: (
       <motion.div
         className="h-full flex flex-col justify-center"
         variants={containerV}
         initial="hidden"
         animate="show"
       >
         <motion.h1
           variants={fadeUp}
           className="text-5xl font-bold text-center mb-8"
         >
           Learning Path <span className="text-cyan-300">Flow</span>
         </motion.h1>

         <motion.div
           className="max-w-7xl mx-auto flex items-center justify-center relative"
           variants={containerV}
         >
           <div className="flex items-center gap-6">
             {/* User Input */}
             <motion.div
               variants={cardV}
               custom={0}
               className="bg-cyan-500/20 backdrop-blur-lg rounded-xl p-4 border border-cyan-300/30 w-48 relative overflow-hidden"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center">
                   <Target className="w-6 h-6 text-white" />
                 </div>
                 <h3 className="text-lg font-bold text-cyan-300 text-center">User Input</h3>
               </div>
               <motion.div
                 className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 via-cyan-300/30 to-cyan-400/20 rounded-xl"
                 animate={{
                   opacity: [0.3, 0.7, 0.3],
                   scale: [0.98, 1.02, 0.98]
                 }}
                 transition={{
                   duration: 3,
                   repeat: Infinity,
                   ease: [0.4, 0, 0.6, 1]
                 }}
               />
             </motion.div>

             {/* Arrow */}
             <motion.div
               className="flex items-center"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 0.3 }}
             >
               <motion.div
                 className="w-8 h-1 bg-gradient-to-r from-cyan-400 to-blue-500"
                 animate={{ scaleX: [1, 1.2, 1] }}
                 transition={{ duration: 2, repeat: Infinity }}
               />
               <motion.div
                 animate={{ x: [0, 4, 0] }}
                 transition={{ duration: 2, repeat: Infinity }}
               >
                 <ChevronRight className="w-6 h-6 text-white" />
               </motion.div>
             </motion.div>

             {/* Blueprint Creation */}
             <motion.div
               variants={cardV}
               custom={1}
               className="bg-blue-500/20 backdrop-blur-lg rounded-xl p-4 border border-blue-300/30 w-48"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <motion.div
                   className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center"
                   animate={{ rotate: [0, 360] }}
                   transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                 >
                   <Brain className="w-6 h-6 text-white" />
                 </motion.div>
                 <h3 className="text-lg font-bold text-blue-300 text-center">Blueprint Creation</h3>
               </div>
             </motion.div>

             {/* Arrow */}
             <motion.div
               className="flex items-center"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 0.6 }}
             >
               <motion.div
                 className="w-8 h-1 bg-gradient-to-r from-blue-500 to-purple-500"
                 animate={{ scaleX: [1, 1.1, 1] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
               />
               <motion.div
                 animate={{ x: [0, 3, 0] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
               >
                 <ChevronRight className="w-6 h-6 text-white" />
               </motion.div>
             </motion.div>

             {/* Query Generation */}
             <motion.div
               variants={cardV}
               custom={2}
               className="bg-purple-500/20 backdrop-blur-lg rounded-xl p-4 border border-purple-300/30 w-48"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <motion.div
                   className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center"
                   animate={{ scale: [1, 1.1, 1] }}
                   transition={{ duration: 2, repeat: Infinity }}
                 >
                   <Zap className="w-6 h-6 text-white" />
                 </motion.div>
                 <h3 className="text-lg font-bold text-purple-300 text-center">Query Generation</h3>
               </div>
             </motion.div>

             {/* Arrow */}
             <motion.div
               className="flex items-center"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 0.9 }}
             >
               <motion.div
                 className="w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500"
                 animate={{ scaleX: [1, 1.1, 1] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1 }}
               />
               <motion.div
                 animate={{ x: [0, 3, 0] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1 }}
               >
                 <ChevronRight className="w-6 h-6 text-white" />
               </motion.div>
             </motion.div>

             {/* Content Pooling */}
             <motion.div
               variants={cardV}
               custom={3}
               className="bg-pink-500/20 backdrop-blur-lg rounded-xl p-4 border border-pink-300/30 w-48"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <motion.div
                   className="w-12 h-12 bg-pink-500 rounded-full flex items-center justify-center"
                   animate={{ rotateY: [0, 180, 360] }}
                   transition={{ duration: 3, repeat: Infinity }}
                 >
                   <Database className="w-6 h-6 text-white" />
                 </motion.div>
                 <h3 className="text-lg font-bold text-pink-300 text-center">Content Pooling</h3>
               </div>
             </motion.div>

             {/* Arrow */}
             <motion.div
               className="flex items-center"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 1.2 }}
             >
               <motion.div
                 className="w-8 h-1 bg-gradient-to-r from-pink-500 to-orange-500"
                 animate={{ scaleX: [1, 1.1, 1] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1.3 }}
               />
               <motion.div
                 animate={{ x: [0, 3, 0] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1.3 }}
               >
                 <ChevronRight className="w-6 h-6 text-white" />
               </motion.div>
             </motion.div>

             {/* Module Selection */}
             <motion.div
               variants={cardV}
               custom={4}
               className="bg-orange-500/20 backdrop-blur-lg rounded-xl p-4 border border-orange-300/30 w-48 relative"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <motion.div
                   className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center"
                   animate={{ scale: [1, 1.1, 1] }}
                   transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
                 >
                   <CheckCircle className="w-6 h-6 text-white" />
                 </motion.div>
                 <h3 className="text-lg font-bold text-orange-300 text-center">Module Selection</h3>
               </div>
             </motion.div>

             {/* Arrow */}
             <motion.div
               className="flex items-center"
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 1.5 }}
             >
               <motion.div
                 className="w-8 h-1 bg-gradient-to-r from-orange-500 to-green-500"
                 animate={{ scaleX: [1, 1.1, 1] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1.6 }}
               />
               <motion.div
                 animate={{ x: [0, 3, 0] }}
                 transition={{ duration: 2, repeat: Infinity, delay: 1.6 }}
               >
                 <ChevronRight className="w-6 h-6 text-white" />
               </motion.div>
             </motion.div>

             {/* Path Complete */}
             <motion.div
               variants={cardV}
               custom={5}
               className="bg-green-500/20 backdrop-blur-lg rounded-xl p-4 border border-green-300/30 w-48 relative overflow-hidden"
               whileHover={{ scale: 1.05 }}
             >
               <div className="flex flex-col items-center gap-2">
                 <motion.div
                   className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center"
                   animate={{ scale: [1, 1.15, 1] }}
                   transition={{ duration: 2, repeat: Infinity }}
                 >
                   <Rocket className="w-6 h-6 text-white" />
                 </motion.div>
                 <h3 className="text-lg font-bold text-green-300 text-center">Path Complete</h3>
               </div>
               <motion.div
                 className="absolute inset-0 bg-gradient-to-r from-green-400/20 via-green-300/30 to-green-400/20 rounded-xl"
                 animate={{
                   opacity: [0.2, 0.6, 0.2],
                   scale: [0.95, 1.05, 0.95]
                 }}
                 transition={{
                   duration: 2.5,
                   repeat: Infinity,
                   ease: [0.4, 0, 0.6, 1]
                 }}
               />
             </motion.div>
           </div>

           {/* Conditional Loop Arrow from Module Selection back to Content Pooling */}
           <motion.div
             className="absolute"
             style={{ top: "120px", left: "calc(50% + 36px)" }}
             initial={{ opacity: 0 }}
             animate={{ opacity: 1 }}
             transition={{ delay: 2.5 }}
           >
             <svg width="520" height="80" viewBox="0 0 520 80">
               <motion.path
                 d="M 480 20 Q 500 20 500 40 Q 500 60 20 60 Q 0 60 0 40 Q 0 20 20 20"
                 fill="none"
                 stroke="rgba(251, 191, 36, 0.8)"
                 strokeWidth="3"
                 strokeDasharray="8,4"
                 initial={{ pathLength: 0 }}
                 animate={{ pathLength: 1 }}
                 transition={{
                   duration: 3,
                   repeat: Infinity,
                   ease: "linear",
                   repeatDelay: 2
                 }}
               />
               <motion.polygon
                 points="15,18 25,23 15,28"
                 fill="rgba(251, 191, 36, 0.9)"
                 animate={{
                   scale: [1, 1.3, 1],
                   opacity: [0.7, 1, 0.7]
                 }}
                 transition={{
                   duration: 2,
                   repeat: Infinity,
                   delay: 2.5
                 }}
               />
             </svg>
             <motion.div
               className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-yellow-500/20 backdrop-blur-lg rounded-lg px-3 py-1 border border-yellow-400/40"
               animate={{
                 scale: [1, 1.05, 1],
                 opacity: [0.8, 1, 0.8]
               }}
               transition={{
                 duration: 3,
                 repeat: Infinity
               }}
             >
               <span className="text-yellow-300 text-sm font-semibold whitespace-nowrap">
                 More modules needed?
               </span>
             </motion.div>
           </motion.div>
         </motion.div>
       </motion.div>
     )
    },
    // Slide 9: Architecture (Tech)
    {
     id: 8,
     title: "Architecture",
     bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
     textColor: "text-white",
     content: (
       <motion.div
         className="space-y-12"
         variants={containerV}
         initial="hidden"
         animate="show"
       >
         <motion.h1
           variants={fadeUp}
           className="text-6xl font-bold text-center mb-8"
         >
           Technical <span className="text-cyan-300">Architecture</span>
         </motion.h1>

         <motion.div
           className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto"
           variants={containerV}
         >
           {[
             {
               icon: <Brain className="w-12 h-12" />,
               title: "AI Engine",
               tech: "OpenAI",
               desc: "Large language model integration"
             },
             {
               icon: <Layers className="w-12 h-12" />,
               title: "Workflow Engine",
               tech: "LangGraph",
               desc: "AI agent orchestration & workflows"
             },
             {
               icon: <Globe className="w-12 h-12" />,
               title: "Frontend",
               tech: "Next.js",
               desc: "React-based web application"
             },
             {
               icon: <Database className="w-12 h-12" />,
               title: "Database",
               tech: "PostgreSQL",
               desc: "Reliable relational data storage"
             },
             {
               icon: <Server className="w-12 h-12" />,
               title: "Task Queue",
               tech: "Celery",
               desc: "Distributed task processing"
             },
             {
               icon: <Zap className="w-12 h-12" />,
               title: "Caching",
               tech: "Redis",
               desc: "High-performance in-memory cache"
             }
           ].map((component, i) => (
             <motion.div
               key={i}
               variants={cardV}
               custom={i}
               className="bg-white/10 backdrop-blur-lg p-6 rounded-xl border border-white/20 hover:border-cyan-300/40 transition-all duration-300"
               whileHover={{
                 y: -8,
                 scale: 1.02,
                 boxShadow: "0 20px 40px rgba(0, 152, 216, 0.2)",
                 transition: {
                   type: "spring",
                   stiffness: 300,
                   damping: 20
                 }
               }}
             >
               <motion.div
                 className="text-cyan-300 mb-4"
                 whileHover={{
                   rotate: [0, 5, -5, 0],
                   transition: {
                     duration: 0.5,
                     ease: [0.4, 0, 0.6, 1]
                   }
                 }}
               >
                 {component.icon}
               </motion.div>
               <h3 className="text-2xl font-bold text-white mb-2">{component.title}</h3>
               <motion.p
                 className="text-lg font-semibold text-cyan-300 mb-2"
                 whileHover={{
                   opacity: [0.8, 1, 0.8],
                   transition: {
                     duration: 0.3,
                     ease: [0.4, 0, 0.6, 1]
                   }
                 }}
               >
                 {component.tech}
               </motion.p>
               <p className="text-sm text-white/80">{component.desc}</p>
             </motion.div>
           ))}
         </motion.div>

         <motion.div
           variants={fadeUp}
           className="bg-white/10 backdrop-blur-lg rounded-xl p-8 max-w-6xl mx-auto border border-white/20"
         >
           <motion.h3
             className="text-2xl font-bold text-cyan-300 mb-6 text-center"
             animate={{
               scale: [1, 1.02, 1]
             }}
             transition={{
               duration: 3,
               repeat: Infinity,
               ease: [0.4, 0, 0.6, 1]
             }}
           >
             Infrastructure & DevOps
           </motion.h3>
           <div className="flex flex-wrap justify-center items-center gap-6">
             {[
               { name: "Python", icon: <Cpu className="w-5 h-5" /> },
               { name: "Docker", icon: <Server className="w-5 h-5" /> },
               { name: "GitHub Actions", icon: <Rocket className="w-5 h-5" /> },
             ].map((tech, i) => (
               <motion.div
                 key={i}
                 className="bg-cyan-500/20 px-6 py-4 rounded-full border border-cyan-300/30 text-lg font-semibold flex items-center gap-3 hover:bg-cyan-500/30 transition-all duration-300"
                 initial={{ opacity: 0, y: 20, scale: 0.9 }}
                 animate={{
                   opacity: 1,
                   y: 0,
                   scale: 1
                 }}
                 transition={{
                   delay: i * 0.2,
                   type: "spring",
                   stiffness: 200,
                   damping: 20
                 }}
                 whileHover={{
                   scale: 1.05,
                   y: -2,
                   transition: {
                     type: "spring",
                     stiffness: 300,
                     damping: 15
                   }
                 }}
               >
                 <motion.div
                   className="text-cyan-300"
                   animate={{
                     rotate: [0, 360]
                   }}
                   transition={{
                     duration: 8,
                     repeat: Infinity,
                     ease: "linear",
                     delay: i * 0.5
                   }}
                 >
                   {tech.icon}
                 </motion.div>
                 <span className="text-white">{tech.name}</span>
               </motion.div>
             ))}
           </div>
         </motion.div>
       </motion.div>
     )
    },

    // Slide 10: Statistics
    {
      id: 9,
      title: "Statistics",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: (
        <motion.div
          className="space-y-12"
          variants={containerV}
          initial="hidden"
          animate="show"
        >
          <motion.h1
            variants={fadeUp}
            className="text-6xl font-bold text-center mb-8"
          >
            Performance <span className="text-cyan-300">Statistics</span>
          </motion.h1>

          <motion.div
            className="grid md:grid-cols-2 gap-12 max-w-6xl mx-auto"
            variants={containerV}
          >
            {/* Without SkillCentral */}
            <motion.div
              variants={cardV}
              className="bg-red-500/10 backdrop-blur-lg rounded-2xl p-8 border border-red-300/30"
            >
              <h3 className="text-3xl font-bold mb-6 text-red-300 text-center">Without Skill Central</h3>
              <div className="space-y-6">
                {[
                  { modules: "5 modules", time: "3:42" },
                  { modules: "10 modules", time: "5:00" },
                  { modules: "15 modules", time: "8:22" }
                ].map((stat, i) => (
                  <motion.div
                    key={i}
                    className="flex justify-between items-center bg-red-500/20 rounded-lg p-4"
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.2 }}
                  >
                    <span className="text-xl font-semibold">{stat.modules}</span>
                    <span className="text-2xl font-bold text-red-300">{stat.time}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* With SkillCentral */}
            <motion.div
              variants={cardV}
              custom={1}
              className="bg-green-500/10 backdrop-blur-lg rounded-2xl p-8 border border-green-300/30"
            >
              <h3 className="text-3xl font-bold mb-6 text-green-300 text-center">With Skill Central</h3>
              <div className="space-y-6">
                {[
                  { modules: "5 modules", time: "1:30", savings: "≈59% faster" },
                  { modules: "10 modules", time: "1:52", savings: "≈63% faster" },
                  { modules: "15 modules", time: "2:51", savings: "≈66% faster" }
                ].map((stat, i) => (
                  <motion.div
                    key={i}
                    className="bg-green-500/20 rounded-lg p-4"
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.2 }}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xl font-semibold">{stat.modules}</span>
                      <span className="text-2xl font-bold text-green-300">{stat.time}</span>
                    </div>
                    <div className="text-center text-green-400 font-semibold">{stat.savings}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="text-center bg-gradient-to-r from-cyan-500/20 to-green-500/20 backdrop-blur-lg rounded-xl p-8 max-w-4xl mx-auto border border-cyan-300/30"
          >
            <motion.p
              className="text-4xl font-bold text-cyan-300 mb-2"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              Average time saved: ≈64%
            </motion.p>
            <p className="text-xl text-white/90">Transform hours of searching into minutes of learning</p>
          </motion.div>
        </motion.div>
      )
    },

    // Slide 11: Future Improvements
    {
     id: 10,
     title: "Future Improvements",
     bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
     textColor: "text-white",
     content: (
       <motion.div
         className="space-y-12 relative"
         variants={containerV}
         initial="hidden"
         animate="show"
       >
         {/* Background Animation */}
         <div className="absolute inset-0 overflow-hidden pointer-events-none">
           {Array.from({ length: 15 }, (_, i) => (
             <motion.div
               key={i}
               className="absolute w-4 h-4 bg-cyan-300/30 rounded-full"
               style={{
                 left: `${Math.random() * 100}%`,
                 top: `${Math.random() * 100}%`,
               }}
               animate={{
                 y: [0, -150, 0],
                 x: [0, Math.random() * 100 - 50, 0],
                 opacity: [0, 0.8, 0],
                 scale: [0.3, 1.2, 0.3]
               }}
               transition={{
                 duration: 8 + Math.random() * 4,
                 repeat: Infinity,
                 ease: [0.4, 0, 0.6, 1],
                 delay: Math.random() * 3
               }}
             />
           ))}
           {Array.from({ length: 10 }, (_, i) => (
             <motion.div
               key={`large-${i}`}
               className="absolute w-8 h-8 bg-white/10 rounded-full"
               style={{
                 left: `${Math.random() * 100}%`,
                 top: `${Math.random() * 100}%`,
               }}
               animate={{
                 y: [0, -200, 0],
                 x: [0, Math.random() * 80 - 40, 0],
                 opacity: [0, 0.4, 0],
                 scale: [0.2, 1, 0.2],
                 rotate: [0, 360, 0]
               }}
               transition={{
                 duration: 12 + Math.random() * 6,
                 repeat: Infinity,
                 ease: [0.4, 0, 0.6, 1],
                 delay: Math.random() * 4
               }}
             />
           ))}
         </div>

         <motion.h1
           variants={fadeUp}
           className="text-6xl font-bold text-center mb-8 relative z-10"
         >
           Future <span className="text-cyan-300">Improvements</span>
         </motion.h1>

         <motion.div
           className="grid md:grid-cols-1 gap-8 max-w-5xl mx-auto relative z-10"
           variants={containerV}
         >
           {[
             {
               icon: <Globe className="w-12 h-12" />,
               title: "Platform Expansion",
               desc: "Connect with Udemy, Coursera, and more learning platforms"
             },
             {
               icon: <Award className="w-12 h-12" />,
               title: "Career Intelligence",
               desc: "Smart recommendations based on your CV and professional goals"
             },
             {
               icon: <Users className="w-12 h-12" />,
               title: "Team Collaboration",
               desc: "Real-time co-editing and shared learning experiences"
             }
           ].map((improvement, i) => (
             <motion.div
               key={i}
               variants={cardV}
               custom={i}
               className="bg-white/10 backdrop-blur-lg p-6 rounded-2xl border border-white/20 flex items-center gap-6 hover:border-cyan-300/40 transition-all duration-300"
               whileHover={{
                 y: -8,
                 scale: 1.02,
                 boxShadow: "0 20px 40px rgba(0, 152, 216, 0.15)",
                 transition: {
                   type: "spring",
                   stiffness: 300,
                   damping: 20
                 }
               }}
             >
               <motion.div
                 className="text-cyan-300 flex-shrink-0"
                 whileHover={{
                   rotate: [0, 10, -10, 0],
                   scale: [1, 1.1, 1],
                   transition: {
                     duration: 0.6,
                     ease: [0.4, 0, 0.6, 1]
                   }
                 }}
               >
                 {improvement.icon}
               </motion.div>
               <div className="flex-1">
                 <motion.h3
                   className="text-2xl font-bold text-white mb-3"
                   whileHover={{
                     x: [0, 5, 0],
                     transition: {
                       duration: 0.3,
                       ease: [0.4, 0, 0.6, 1]
                     }
                   }}
                 >
                   {improvement.title}
                 </motion.h3>
                 <p className="text-lg text-white/80">
                   {improvement.desc}
                 </p>
               </div>
             </motion.div>
           ))}
         </motion.div>

         {/* Extra spacing between last improvement card and bottom section */}
         <div className="h-16"></div>

         <motion.div
           variants={fadeUp}
           className="text-center bg-white/10 backdrop-blur-lg rounded-xl p-6 max-w-4xl mx-auto border border-white/20 relative z-10"
         >
           <motion.p
             className="text-2xl font-semibold text-white mb-4"
             animate={{
               scale: [1, 1.02, 1]
             }}
             transition={{
               duration: 3,
               repeat: Infinity,
               ease: [0.4, 0, 0.6, 1]
             }}
           >
             🚀 Building the future of personalized learning
           </motion.p>
           <motion.p
             className="text-lg text-white/80"
             animate={{
               opacity: [0.7, 1, 0.7]
             }}
             transition={{
               duration: 2,
               repeat: Infinity,
               ease: [0.4, 0, 0.6, 1]
             }}
           >
             Every feature driven by your success
           </motion.p>
         </motion.div>
       </motion.div>
     )
    },

      {
       id: 12,
       title: "Our Team",
       bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
       textColor: "text-white",
       content: (
         <motion.div
           className="text-center space-y-12"
           variants={containerV}
           initial="hidden"
           animate="show"
         >
           <motion.h1
             variants={fadeUp}
             className="text-6xl font-bold mb-8"
           >
             Meet Our <span className="text-cyan-300">Team</span>
           </motion.h1>

           <motion.div
             variants={fadeUp}
             className="max-w-5xl mx-auto"
           >
             <motion.div
               className="relative overflow-hidden rounded-3xl border-4 border-white/20 shadow-2xl backdrop-blur-lg bg-white/5"
               whileHover={{
                 scale: 1.02,
                 boxShadow: "0 25px 50px rgba(0, 152, 216, 0.3)"
               }}
               animate={{
                 boxShadow: [
                   "0 20px 40px rgba(0, 152, 216, 0.2)",
                   "0 25px 45px rgba(0, 152, 216, 0.25)",
                   "0 20px 40px rgba(0, 152, 216, 0.2)"
                 ]
               }}
               transition={{
                 boxShadow: { duration: 3, repeat: Infinity, ease: "easeInOut" },
                 scale: { type: "spring", stiffness: 300, damping: 20 }
               }}
             >
               <Image
                 src="/team-picture.png"
                 alt="Skill Central Team"
                 width={800}
                 height={500}
                 className="w-full h-auto object-cover"
                 style={{
                   maxHeight: '500px',
                   width: '100%'
                 }}
               />
               <motion.div
                 className="absolute inset-0 bg-gradient-to-t from-[#203878]/20 via-transparent to-transparent"
                 animate={{
                   opacity: [0.3, 0.5, 0.3]
                 }}
                 transition={{
                   duration: 4,
                   repeat: Infinity,
                   ease: "easeInOut"
                 }}
               />
             </motion.div>
           </motion.div>

           <motion.div
             variants={fadeUp}
             className="max-w-4xl mx-auto"
           >
             <motion.p
               className="text-2xl text-white/90 leading-relaxed"
               animate={{
                 opacity: [0.9, 1, 0.9]
               }}
               transition={{
                 duration: 3,
                 repeat: Infinity,
                 ease: "easeInOut"
               }}
             >
               Passionate innovators dedicated to transforming how the world learns
             </motion.p>
           </motion.div>

           <motion.div
             variants={fadeUp}
             className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto"
           >
             {[
               {
                 icon: <Brain className="w-8 h-8" />,
                 title: "Innovation",
                 desc: "Cutting-edge AI solutions"
               },
               {
                 icon: <Users className="w-8 h-8" />,
                 title: "Collaboration",
                 desc: "Diverse expertise united"
               },
               {
                 icon: <Target className="w-8 h-8" />,
                 title: "Impact",
                 desc: "Transforming education"
               }
             ].map((value, i) => (
               <motion.div
                 key={i}
                 variants={cardV}
                 custom={i}
                 className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
                 whileHover={{ y: -4, scale: 1.02 }}
               >
                 <div className="text-cyan-300 mb-4 flex justify-center">{value.icon}</div>
                 <h3 className="text-xl font-bold mb-2">{value.title}</h3>
                 <p className="text-white/80">{value.desc}</p>
               </motion.div>
             ))}
           </motion.div>
         </motion.div>
       )
      },

    // Slide 12: Call to Action
    {
      id: 11,
      title: "Call to Action",
      bgColor: "from-[#203878] via-[#134B8E] to-[#0098D8]",
      textColor: "text-white",
      content: (
        <motion.div
          className="text-center space-y-16"
          variants={containerV}
          initial="hidden"
          animate="show"
        >
          <motion.h1
            variants={fadeUp}
            className="text-7xl font-bold mb-8"
          >
            Ready to <span className="text-cyan-300">Level Up</span>
          </motion.h1>

          <motion.h2
            variants={fadeUp}
            className="text-4xl font-semibold text-white/90 mb-12"
          >
            Your Learning?
          </motion.h2>

          <motion.div
            variants={fadeUp}
            className="max-w-4xl mx-auto"
          >
            <Link href="/dashboard">
              <motion.button
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-3xl font-bold py-6 px-12 rounded-2xl shadow-2xl border-2 border-white/20 backdrop-blur-lg"
                whileHover={{
                  scale: 1.1,
                  boxShadow: "0 25px 50px rgba(0, 152, 216, 0.5)",
                  y: -8
                }}
                whileTap={{ scale: 0.95 }}
                animate={{
                  boxShadow: [
                    "0 10px 30px rgba(0, 152, 216, 0.3)",
                    "0 15px 40px rgba(0, 152, 216, 0.4)",
                    "0 10px 30px rgba(0, 152, 216, 0.3)"
                  ]
                }}
                transition={{
                  boxShadow: { duration: 2, repeat: Infinity },
                  type: "spring",
                  stiffness: 200
                }}
              >
                <div className="flex items-center gap-4">
                  <Rocket className="w-10 h-10" />
                  Start Your Journey
                  <ArrowRight className="w-10 h-10" />
                </div>
              </motion.button>
            </Link>
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto mt-16"
          >
            {[
              {
                icon: <Target className="w-8 h-8" />,
                title: "Personalized",
                desc: "Tailored to your goals"
              },
              {
                icon: <Zap className="w-8 h-8" />,
                title: "Efficient",
                desc: "64% time savings"
              },
              {
                icon: <Users className="w-8 h-8" />,
                title: "Collaborative",
                desc: "Team-ready features"
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                variants={cardV}
                custom={i}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
                whileHover={{ y: -4 }}
              >
                <div className="text-cyan-300 mb-4 flex justify-center">{feature.icon}</div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-white/80">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="text-2xl text-white/90 max-w-3xl mx-auto"
          >
          </motion.div>
        </motion.div>
      )
    }
  ];

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        setCurrentSlide(prev => prev === 0 ? slides.length - 1 : prev - 1);
      } else if (e.key === 'ArrowRight') {
        setCurrentSlide(prev => (prev + 1) % slides.length);
      } else if (e.key === 'Escape') {
        setShowModal(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [slides.length]);

  const nextSlide = (): void => setCurrentSlide((prev) => (prev + 1) % slides.length);
  const prevSlide = (): void => setCurrentSlide((prev) => prev === 0 ? slides.length - 1 : prev - 1);
  const goToSlide = (index: number): void => setCurrentSlide(index);

  const currentSlideData = slides[currentSlide];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Particles Background */}
      <ParticlesBackground />

      {/* Main Content */}
      <div className={`min-h-screen bg-gradient-to-br ${currentSlideData.bgColor} ${currentSlideData.textColor} relative z-10`}>
        {/* Header Controls */}
        <motion.div
          className="absolute top-6 left-6 right-6 z-30 flex justify-between items-center"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center space-x-4">
            <Link href="/dashboard">
              <motion.button
                className="bg-white/20 backdrop-blur-lg rounded-lg px-4 py-3 hover:bg-white/30 transition-colors flex items-center space-x-2"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <ChevronLeft className="w-5 h-5" />
                <span className="font-semibold">Back to Dashboard</span>
              </motion.button>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <motion.button
              onClick={() => {
                setModalContent({
                  title: "Navigation Help",
                  content: (
                    <div className="space-y-4 text-gray-700">
                      <h4 className="font-semibold">Keyboard Shortcuts:</h4>
                      <ul className="space-y-2 text-sm">
                        <li><kbd className="bg-gray-200 px-2 py-1 rounded">←</kbd> Previous slide</li>
                        <li><kbd className="bg-gray-200 px-2 py-1 rounded">→</kbd> Next slide</li>
                        <li><kbd className="bg-gray-200 px-2 py-1 rounded">Esc</kbd> Close modal</li>
                      </ul>
                      <p className="text-sm">Click on any slide indicator to jump directly to that slide.</p>
                    </div>
                  )
                });
                setShowModal(true);
              }}
              className="bg-white/20 backdrop-blur-lg rounded-full p-3 hover:bg-white/30 transition-colors"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <Info className="w-6 h-6" />
            </motion.button>
          </div>
        </motion.div>

        {/* Slide Content */}
        <div className="flex items-center justify-center min-h-screen pt-24 pb-32 px-6">
          <div className="max-w-7xl mx-auto w-full">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentSlide}
                initial={{ opacity: 0, x: 300 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -300 }}
                transition={{ type: "spring", stiffness: 200, damping: 30 }}
                className="w-full"
              >
                {currentSlideData.content}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Navigation Controls */}
        <motion.button
          onClick={prevSlide}
          className="fixed left-0 top-0 w-24 h-full z-10 flex items-center justify-start pl-6 hover:bg-white/10 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <ChevronLeft className="w-8 h-8 text-white/80 hover:text-white" />
        </motion.button>

        <motion.button
          onClick={nextSlide}
          className="fixed right-0 top-0 w-24 h-full z-10 flex items-center justify-end pr-6 hover:bg-white/10 transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <ChevronRight className="w-8 h-8 text-white/80 hover:text-white" />
        </motion.button>

        {/* Slide Indicators */}
        <div className="absolute bottom-6 left-0 right-0 z-20 flex justify-center">
          <motion.div
            className="flex space-x-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {slides.map((_, index) => (
              <motion.button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index === currentSlide 
                    ? 'bg-white scale-125' 
                    : 'bg-white/50 hover:bg-white/75'
                }`}
                whileHover={{ scale: 1.2 }}
                whileTap={{ scale: 0.9 }}
              />
            ))}
          </motion.div>
        </div>

        {/* Progress Bar */}
        <div className="absolute bottom-0 left-0 w-full h-1 bg-white/20">
          <motion.div
            className="h-full bg-white"
            initial={{ width: 0 }}
            animate={{ width: `${((currentSlide + 1) / slides.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && modalContent && (
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
          >
            <motion.div
              className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900">{modalContent.title}</h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="text-gray-700">
                {modalContent.content}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SkillCentralPresentation;