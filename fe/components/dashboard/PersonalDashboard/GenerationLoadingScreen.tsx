"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {ArrowLeft, Sparkles} from 'lucide-react';
import { Button } from '@/components/common/Button';
import Image from 'next/image';

interface GenerationLoadingScreenProps {
  messages: string[];
  onBackToDashboard: () => void;
}

// Subcomponent for the animated text
const AnimatedMessage = ({ message, isVisible }: { message: string, isVisible: boolean }) => {
    const variants = {
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.02 } },
    };

    const letterVariant = {
        hidden: { opacity: 0 },
        visible: { opacity: 1 },
    };

    if (!isVisible) return null;

    return (
        <motion.span
            variants={variants}
            initial="hidden"
            animate="visible"
            aria-label={message}
        >
            {message.split("").map((char, index) => (
                <motion.span key={`${char}-${index}`} variants={letterVariant}>
                    {char}
                </motion.span>
            ))}
        </motion.span>
    );
};


export default function GenerationLoadingScreen({ messages, onBackToDashboard }: GenerationLoadingScreenProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex(prev => (prev < messages.length ? prev + 1 : prev));
    }, 2500); // Time each step is "in progress"
    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}

      className="relative z-10 bg-gray-200 backdrop-blur-lg rounded-2xl border border-white shadow-2xl p-8 w-full max-w-lg overflow-hidden flex flex-col items-center"
    >
      <motion.div
        className="absolute top-0 left-0 w-full h-full z-[-1]"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%)',
          backgroundSize: '200% 100%',
        }}
        animate={{ backgroundPosition: ['-200% 0%', '200% 0%'] }}
        transition={{
            duration: 2.5,
            repeat: Infinity,
            ease: 'linear',
        }}
      />

      <motion.div
        className="mx-auto mb-6 w-20 h-20 bg-primary rounded-full flex items-center justify-center border-2 border-primary"
      >
        <Image
          src="/logo.png"
          alt="Site Logo"
          width={52}
          height={44}
          priority
          style={{
              width: 'auto',
              height: '44px',
              maxWidth: '52px',
              maxHeight: '52px'
            }}
        />
      </motion.div>

      <h2 className="text-2xl font-bold text-gray-700 mb-2">Creating Your Learning Path</h2>
      <p className="text-neutral mb-4 flex items-center justify-center">
        <Sparkles className="w-4 h-4 mr-2 text-primary" />
        AI is generating your personalized path...
      </p>

      <div className="w-full bg-gray-400 rounded-full h-2 my-4 overflow-hidden">
        <motion.div
          className="bg-primary h-2 rounded-full w-2/5"
          initial={{ x: "-150%" }}
          animate={{ x: "400%" }}
          transition={{
            duration: 2.5,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      </div>

      <div className="text-neutral space-y-3 mb-8 flex flex-col items-start">
        {messages.map((msg, index) => (
          <motion.div
            key={msg}
            className="flex items-center space-x-3"
            initial={{ opacity: 0.4 }}
            animate={{ opacity: currentMessageIndex >= index ? 1 : 0.4 }}
            transition={{ duration: 0.5 }}
          >
            <div className="w-5 h-5 flex-shrink-0 flex items-center justify-center">
              <AnimatePresence>
                {currentMessageIndex > index && (
                  <motion.div key="check" className="w-5 h-5 flex items-center justify-center">
                    <motion.div
                        className="w-1 h-1 bg-primary rounded-full"
                        animate={{ scale: [1, 1.5, 1] }}
                        transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                    />
                  </motion.div>
                )}
                {currentMessageIndex === index && (
                  <motion.div key="progress" className="w-5 h-5 flex items-center justify-center">
                    <motion.div
                        className="w-1 h-1 bg-primary rounded-full"
                        animate={{ scale: [1, 1.8, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
                    />
                  </motion.div>
                )}
                {currentMessageIndex < index && (
                  <motion.div key="pending" className="w-5 h-5 flex items-center justify-center">
                    <div className="w-1 h-1 bg-gray-300 rounded-full" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <AnimatedMessage message={msg} isVisible={currentMessageIndex >= index} />
          </motion.div>
        ))}
      </div>

      <Button variant="hollow" onClick={onBackToDashboard} className="font-semibold">
        <ArrowLeft className="w-4 h-4" strokeWidth={2.5} /> Back to Dashboard
      </Button>
    </motion.div>
  );
}