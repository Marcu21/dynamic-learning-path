import { motion, AnimatePresence } from 'framer-motion';
import { Loader2Icon } from 'lucide-react';
import { useState, useEffect } from 'react';

const messages = [
    "Analyzing previous modules...",
    "Crafting new learning objectives...",
    "Finalizing the module structure...",
];

export const GeneratingModuleCard = () => {
    const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentMessageIndex(prev => (prev + 1) % messages.length);
        }, 2000);
        
        return () => {
            clearInterval(interval);
        };
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0, height: 0, y: 20, scale: 0.95 }}
            animate={{ 
                opacity: 1, 
                height: 'auto', 
                y: 0, 
                scale: 1,
                transition: { 
                    duration: 0.6, 
                    ease: 'easeOut',
                    height: { duration: 0.4, ease: 'easeInOut' }
                }
            }}
            exit={{ 
                opacity: 0, 
                height: 0, 
                scale: 0.95,
                transition: { 
                    duration: 0.4, 
                    ease: 'easeIn',
                    height: { duration: 0.3, ease: 'easeInOut' }
                }
            }}
            className="bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 rounded-xl shadow-lg border-2 border-primary/20 mb-4 overflow-hidden"
        >
            <div className="p-6 flex items-center space-x-4">
                <motion.div
                    className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                    <Loader2Icon className="w-6 h-6 text-primary" />
                </motion.div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-display font-semibold text-primary">
                        AI is crafting your new module...
                    </h3>
                    <div className="text-sm text-neutral-secondary-light h-5 mt-1 relative">
                      <AnimatePresence mode="wait">
                        <motion.p
                          key={currentMessageIndex}
                          className="absolute inset-0"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.35, ease: [0.22, 0.61, 0.36, 1] }}
                        >
                          {messages[currentMessageIndex]}
                        </motion.p>
                      </AnimatePresence>
                    </div>
                </div>
            </div>
            <div className="w-full bg-neutral-accent-light rounded-full h-2 mt-4 relative overflow-hidden">
                <motion.div
                    className="absolute inset-0 h-full bg-gradient-to-r from-primary to-accent"
                    initial={{ x: "-100%" }}
                    animate={{ x: "100%" }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                />
            </div>
        </motion.div>
    );
};