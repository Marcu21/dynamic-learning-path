import {useState} from 'react';
import {motion, AnimatePresence} from 'framer-motion';
import {ChevronDown} from 'lucide-react';
import {FC} from 'react';
import {GenerationDetailsCardProps} from '@/components/learning-path/GenerationDetailsCard/types';

const GenerationDetailsCard: FC<GenerationDetailsCardProps> = ({title, icon: Icon, children, defaultOpen = false}) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    const cardVariants = {
        open: {opacity: 1, y: 0},
        collapsed: {opacity: 0, y: -10},
    };

    return (
        <motion.div
            layout
            transition={{duration: 0.4, ease: [0.04, 0.62, 0.23, 0.98]}}
            className="bg-white rounded-xl shadow-lg"
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex justify-between items-center p-4 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
                <div className="flex items-center">
                    <Icon className="w-5 h-5 mr-3 text-primary"/>
                    <h3 className="text-lg font-display font-semibold text-neutral-dark">
                        {title}
                    </h3>
                </div>
                <motion.div
                    animate={{rotate: isOpen ? 180 : 0}}
                    transition={{duration: 0.2}}
                >
                    <ChevronDown className="w-5 h-5 text-neutral-secondary-light"/>
                </motion.div>
            </button>

            <div className="overflow-hidden">
                <AnimatePresence mode={"wait"}>
                    {isOpen && (
                        <motion.section
                            key="content"
                            initial="collapsed"
                            animate="open"
                            exit="collapsed"
                            variants={cardVariants}
                            transition={{duration: 0.3, ease: 'easeOut'}}
                            className="px-4 pb-4"
                        >
                            {children}
                        </motion.section>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
export default GenerationDetailsCard;