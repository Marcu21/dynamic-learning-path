import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LoaderCircle, Sparkles } from 'lucide-react';
import { teamStyles } from './styles';

const generatingMessages = [
    "Analyzing team goals...",
    "Structuring learning modules...",
    "Finding optimal resources...",
    "Calibrating difficulty...",
];

export default function GeneratingPathCard() {
    const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentMessageIndex(prev => (prev + 1) % generatingMessages.length);
        }, 2500);
        return () => clearInterval(interval);
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`${teamStyles.pathCard} pointer-events-none`}
        >
            <div className="flex flex-col h-full">
                <div className="flex items-start space-x-4">
                    <div className="p-3 mt-1 rounded-xl bg-gradient-to-br from-[#5E35B1]/20 to-[#8E44AD]/10 text-[#380A63] relative overflow-hidden">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                        >
                            <LoaderCircle className="w-6 h-6" />
                        </motion.div>
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-bold text-[#380A63]">
                            AI is Crafting a New Path...
                        </h3>
                        <p className="text-[#380A63] text-sm mt-1 h-5 relative overflow-hidden">
                          <AnimatePresence mode="wait">
                            <motion.span
                              key={currentMessageIndex}
                              className="absolute inset-0"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              transition={{ duration: 0.35, ease: [0.22, 0.61, 0.36, 1] }}
                            >
                              {generatingMessages[currentMessageIndex]}
                            </motion.span>
                          </AnimatePresence>
                        </p>
                    </div>
                </div>

                <div className="mt-auto pt-4 space-y-2">
                    <div className="w-full h-2 bg-[#380A63]/10 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-[#5E35B1] to-[#8E44AD]"
                            initial={{ x: '-100%' }}
                            animate={{ x: '100%' }}
                            transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: 'easeInOut',
                            }}
                        />
                    </div>
                    <div className="flex items-center text-sm text-neutral-dark">
                        <Sparkles className="w-4 h-4 mr-1 text-amber-500" />
                        <span>Generation in progress...</span>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}