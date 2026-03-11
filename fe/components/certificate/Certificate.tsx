"use client"

import React, { useRef, useState } from "react";
import {motion, AnimatePresence, Variants} from "framer-motion";
import { X, Download, Share2, Award, Star, Calendar, BookOpen, Trophy } from "lucide-react";
import { ButtonProps, CertificateProps } from "@/components/certificate/types";

const Button: React.FC<ButtonProps> = ({ children, className, ...props }) => (
  <button className={`transition-colors duration-200 ${className}`} {...props}>
    {children}
  </button>
);

export default function Certificate({
  isOpen,
  onClose,
  userName,
  pathTitle,
  completionDate = new Date(),
  totalModules,
  estimatedDays,
}: CertificateProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const certificateRef = useRef<HTMLDivElement>(null);

  const formatFullName = (username: string): string => {
    if (!username) return "";
    return username
      .split(/[_.]/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const fullName = formatFullName(userName);

  const handleDownload = async () => {
    if (!certificateRef.current) {
      alert("Could not find the certificate element to download.");
      return;
    }
    setIsDownloading(true);
    try {
      const htmlToImage = await import("html-to-image");
      const dataUrl = await htmlToImage.toPng(certificateRef.current, {
        quality: 1,
        pixelRatio: 3, // High pixel ratio for sharp image
        backgroundColor: '#ffffff',
      });
      const link = document.createElement("a");
      link.download = `certificate_${pathTitle.replace(/\s+/g, '_').toLowerCase()}.png`;
      link.href = dataUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      alert("An error occurred while downloading the certificate.");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleShare = async () => {
  if (!certificateRef.current) {
    alert("Could not find the certificate element to share.");
    return;
  }
  setIsSharing(true);
  try {
    const htmlToImage = await import("html-to-image");

    const blob = await htmlToImage.toBlob(certificateRef.current, {
      quality: 1,
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    });

    if (!blob) {
      throw new Error('Could not generate certificate image.');
    }

    const fileName = `certificate_${pathTitle.replace(/\s+/g, '_').toLowerCase()}.png`;
    const file = new File([blob], fileName, { type: 'image/png' });

    const shareText = `I just earned a Certificate of Achievement for completing the "${pathTitle}" learning path on Dynamic Learning Path! 🎉`;
    const shareData = {
      title: "Certificate of Achievement",
      text: shareText,
      files: [file],
    };

    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      await navigator.share(shareData);
    } else {
      alert("Your browser doesn't support sharing images directly. The achievement text has been copied to your clipboard!");
      navigator.clipboard.writeText(`${shareText} ${window.location.href}`);
    }
  } catch (error) {
    if ((error as Error).name !== 'AbortError') {
        alert("An error occurred while sharing the certificate.");
    }
  } finally {
    setIsSharing(false);
  }
};

  // Animation variants for staggered effect
  const statsContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 1.2,
      },
    },
  };

  const statItemVariants: Variants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100,
      },
    },
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/70 backdrop-blur-lg z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[95vh] overflow-y-auto flex flex-col"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 md:p-6 flex-grow">
              {/* This is the element to be captured */}
              <div ref={certificateRef} className="bg-white p-2">
                <div className="border-4 border-amber-500 rounded-xl p-1 bg-white relative">
                  <div className="border-2 border-amber-500 rounded-lg p-4 md:p-8 bg-gray-50 relative flex aspect-[1.7/1] overflow-hidden">

                    {/* Decorative elements in the background */}
                    <div className="absolute inset-0 bg-gradient-radial from-white via-blue-50 to-amber-50 opacity-50 z-0"></div>
                    <div className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 rounded-full bg-amber-400/10 blur-3xl z-0"></div>
                    <div className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 rounded-full bg-blue-400/10 blur-3xl z-0"></div>

                    <Award className="absolute top-6 left-6 w-14 h-14 text-amber-400/30 z-0" strokeWidth={1} />
                    <Award className="absolute top-6 right-6 w-14 h-14 text-amber-400/30 z-0" strokeWidth={1} />
                    <Star className="absolute bottom-6 left-6 w-12 h-12 text-blue-500/20 z-0" strokeWidth={1}/>
                    <Star className="absolute bottom-6 right-6 w-12 h-12 text-blue-500/20 z-0" strokeWidth={1}/>

                    {/* Left Column */}
                    <motion.div
                      className="w-[41%] flex flex-col justify-center items-center text-center pr-8 border-r-2 border-gray-200/80 gap-y-[4.7rem] z-10"
                      initial={{ opacity: 0, x: -50 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.8, delay: 0.2 }}
                    >
                      <div className="w-full">
                        <h1 className="text-[1.75rem] font-bold text-gray-800 tracking-wide leading-tight">
                           <span className="font-bold text-neutral-dark">Certificate of Achievement</span>
                        </h1>
                        <div className="w-32 h-0.5 bg-amber-500 mx-auto mt-2 rounded-full"></div>
                      </div>

                      <motion.div
                        className="relative p-4"
                        whileHover={{ scale: 1.05 }}
                        transition={{ type: 'spring', stiffness: 150, delay: 0 }}
                      >
                        <Trophy className="text-amber-500 w-32 h-32 drop-shadow-lg" strokeWidth={1.1} />
                      </motion.div>

                      <div className="w-full text-xs text-neutral-dark">
                        <p className="font-bold text-md mb-1">Dynamic Learning Path</p>
                        <p className="text-neutral-dark">Authorized Certificate</p>
                        <div className="w-32 border-b border-gray-400 mx-auto my-1"></div>
                        <p className="mt-2 text-neutral-dark flex items-center justify-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            Issued on {completionDate.toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" })}
                          </span>
                        </p>
                      </div>
                    </motion.div>

                    {/* Right Column */}
                    <motion.div
                      className="w-[59%] flex flex-col justify-center items-center text-center pl-8 z-10"
                      initial={{ opacity: 0, x: 50 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.8, delay: 0.4 }}
                    >
                      <p className="text-xl text-neutral-dark mb-4">This certificate is proudly presented to</p>

                      <motion.h2
                        className="text-4xl md:text-4xl font-bold text-blue-800 mb-6 border-b-2 border-blue-200 pb-2 inline-block"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.9, type: "spring" }}
                      >
                        {fullName}
                      </motion.h2>

                      <p className="text-xl text-neutral-dark mb-4">For the successful completion of the learning path</p>

                      <h3 className="text-3xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 mb-12">
                        "{pathTitle}"
                      </h3>

                      {/* Stats Section */}
                      <motion.div
                        className="flex justify-center gap-6"
                        variants={statsContainerVariants}
                        initial="hidden"
                        animate="visible"
                      >
                        <motion.div
                          variants={statItemVariants}
                          whileHover={{ scale: 1.05 }}
                          className="text-center p-4 bg-white/80 rounded-lg shadow-sm border border-gray-200/80 w-36"
                        >
                          <BookOpen className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                          <div className="text-2xl font-bold text-gray-800">{totalModules}</div>
                          <div className="text-sm text-neutral-dark">Modules</div>
                        </motion.div>
                        {estimatedDays && (
                          <motion.div
                            variants={statItemVariants}
                            whileHover={{ scale: 1.05 }}
                            className="text-center p-4 bg-white/80 rounded-lg shadow-sm border border-gray-200/80 w-36"
                          >
                            <Calendar className="w-8 h-8 text-green-600 mx-auto mb-2" />
                            <div className="text-2xl font-bold text-gray-800">{estimatedDays}</div>
                            <div className="text-sm text-neutral-dark">Days</div>
                          </motion.div>
                        )}
                        <motion.div
                          variants={statItemVariants}
                          whileHover={{ scale: 1.05 }}
                          className="text-center p-4 bg-white/80 rounded-lg shadow-sm border border-gray-200/80 w-36"
                        >
                          <Trophy className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                          <div className="text-2xl font-bold text-gray-800">100%</div>
                          <div className="text-sm text-neutral-dark">Completion</div>
                        </motion.div>
                      </motion.div>
                    </motion.div>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 p-4 bg-gray-50 border-t border-gray-200">
              <Button
                onClick={handleDownload}
                disabled={isDownloading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary-dark disabled:bg-purple-300 disabled:cursor-not-allowed"
              >
                <Download className="w-5 h-5" />
                <span>{isDownloading ? "Downloading..." : "Download Certificate"}</span>
              </Button>
              <Button
                onClick={handleShare}
                disabled={isSharing}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-primary text-primary font-semibold bg-transparent hover:bg-primary/10 disabled:border-purple-300 disabled:text-purple-300 disabled:cursor-not-allowed"
              >
                <Share2 className="w-5 h-5" />
                <span>{isSharing ? "Preparing..." : "Share Achievement"}</span>
              </Button>

              <Button onClick={onClose} aria-label="Close" className="sm:flex-none flex items-center justify-center p-3 rounded-full text-gray-500 hover:bg-gray-200 hover:text-gray-800">
                  <X className="w-5 h-5" />
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}