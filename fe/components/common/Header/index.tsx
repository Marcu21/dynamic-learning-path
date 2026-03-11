"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import Image from "next/image";
import { AnimatePresence, motion, Variants } from "framer-motion";
import type { HeaderProps, Particle } from "@/components/common/Header/types";
import * as anim from "@/components/common/Header/animations";
import * as styles from "@/components/common/Header/styles";
import {Menu, Sparkles, Bell, LogOut, UserCircle, GraduationCap} from "lucide-react";
import { useRouter } from 'next/router';
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationContext";
import { NotificationPanel } from "@/components/common/Header/NotificationPanel";
import { useOnClickOutside } from "@/hooks/useOnClickOutside";


const UserDisplayV1 = ({ displayUsername }: { displayUsername: string }) => {
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { logout, user } = useAuth();

  useOnClickOutside(dropdownRef as RefObject<HTMLElement>, () => setDropdownOpen(false));

  const handleProfileClick = () => {
    router.push('/profile');
    setDropdownOpen(false);
  };

  const handleLogout = () => {
    setDropdownOpen(false);
    logout();
    router.push('/login');
  };

  const formatFullName = (username: string): string => {
    if (!username) return "";
    return (user?.full_name || username)
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const fullName = formatFullName(displayUsername);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const localAnim = {
    itemVariants: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    },
    spring: { type: "spring", stiffness: 400, damping: 25 },
  } as const;

  const dropdownVariants: Variants = {
      hidden: { opacity: 0, y: -10, scale: 0.95 },
      visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.15, ease: "easeOut" } },
      exit: { opacity: 0, y: -10, scale: 0.95, transition: { duration: 0.1, ease: "easeIn" } }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <motion.div
        className="flex items-center gap-3 cursor-pointer"
        variants={localAnim.itemVariants}
        whileHover={{ scale: 1.02 }}
        transition={localAnim.spring}
        onClick={() => setDropdownOpen(prev => !prev)}
      >
        <div className="relative">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-md">
            {getInitials(fullName)}
          </div>
          <motion.div
            className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-sm"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <div className="w-2.5 h-2.5 bg-green-400 rounded-full" />
          </motion.div>
        </div>
        <div className="flex flex-col">
          <motion.span
            className="font-medium text-gray-800 text-sm"
            animate={{ opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
          >
            {fullName}
          </motion.span>
          <span className="text-xs text-gray-500">Online</span>
        </div>
      </motion.div>
      <AnimatePresence>
        {isDropdownOpen && (
           <motion.div
             className="absolute top-full right-0 mt-2 w-48 bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden"
             variants={dropdownVariants}
             initial="hidden"
             animate="visible"
             exit="exit"
           >
             <div className="p-1.5">
               <button
                  onClick={handleProfileClick}
                  className="flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-purple-100/50 hover:text-purple-700 transition-colors duration-150"
               >
                 <UserCircle className="w-5 h-5" />
                 <span>My Profile</span>
               </button>
               <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-red-100/50 hover:text-red-700 transition-colors duration-150"
               >
                 <LogOut className="w-5 h-5" />
                 <span>Logout</span>
               </button>
             </div>
           </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};


export default function Header({ username, onOpenSidebar }: HeaderProps) {
  const { user } = useAuth();
  const displayUsername = username || user?.username || user?.email || '';

  const { unreadCount } = useNotifications();
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const router = useRouter();

  useOnClickOutside(panelRef as RefObject<HTMLDivElement>, () => setIsPanelOpen(false));

  const [particles, setParticles] = useState<Particle[]>([]);
  useEffect(() => {
    setParticles(
      Array.from({ length: 15 }, () => ({
        left: Math.random() * 100,
        top: Math.random() * 100,
      }))
    );
  }, []);

  const buttonStyle = "relative p-2 rounded-full flex items-center justify-center cursor-pointer group hover:bg-slate-100 transition-colors duration-150";

  return (
    <div className={`${styles.wrapper} isolation-isolate`}>
      <div className={styles.bgBlobsWrapper}>
        <motion.div
          className="absolute -top-20 -left-20 w-40 h-40 rounded-full filter blur-2xl opacity-20 mix-blend-multiply"
          style={{ background: "linear-gradient(45deg, #667eea, #764ba2)" }}
          animate={{ x: [0, 30, -20, 0], y: [0, -15, 20, 0], scale: [1, 1.3, 0.8, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -top-20 -right-20 w-48 h-48 rounded-full filter blur-xl opacity-25 mix-blend-multiply"
          style={{ background: "linear-gradient(135deg, #ffecd2, #fcb69f)" }}
          animate={{ x: [0, -40, 25, 0], y: [0, 25, -15, 0], scale: [1, 0.7, 1.4, 1] }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full filter blur-2xl opacity-15 mix-blend-multiply"
          style={{ background: "linear-gradient(225deg, #a8edea, #fed6e3)" }}
          animate={{ rotate: [0, 360], scale: [1, 1.5, 1] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        />
        {particles.map((p, i) => (
          <motion.div
            key={i}
            className={styles.particle}
            style={{ left: `${p.left}%`, top: `${p.top}%` }}
            animate={{ y: [0, -15, 0], opacity: [0.2, 0.8, 0.2], scale: [1, 1.5, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: i * 0.2 }}
          />
        ))}
      </div>

      <motion.header
        className="bg-white border-b border-slate-200 shadow-md sticky top-0 z-50"
        initial="hidden"
        animate="visible"
        variants={anim.headerVariants}
      >
        <div className="flex items-center justify-between w-full py-4">
          <div className="flex items-center pl-6">
            {onOpenSidebar && (
              <motion.button
                onClick={onOpenSidebar}
                className={`${buttonStyle} mr-4`}
                variants={anim.iconVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
                title="Open team sidebar"
              >
                <Menu className="w-6 h-6 text-purple-500 group-hover:text-purple-700 transition-colors" />
              </motion.button>
            )}
            <motion.div
              className={`${styles.logoSection} cursor-pointer`}
              variants={anim.itemVariants}
              onClick={() => router.push('/dashboard')}
            >
              <motion.div
                className={styles.logoWrapper}
                variants={anim.iconVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
              >
                <motion.div
                  className={styles.logoBadge}
                  animate={{
                    boxShadow: [
                      "0 0 20px rgba(147,51,234,0.3)",
                      "0 0 30px rgba(236,72,153,0.5)",
                      "0 0 20px rgba(147,51,234,0.3)",
                    ],
                  }}
                  transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                >
                  <GraduationCap
                    size={24}
                    color="#ffffff"
                    className="text-white shrink-0"
                    aria-label="Site Logo"
                    strokeWidth={2}
                  />
                </motion.div>
              </motion.div>
              <motion.div variants={anim.itemVariants}>
                <motion.h1
                  className={styles.titleGradient}
                  whileHover={{ scale: 1.05 }}
                  transition={{
                    scale: { type: "spring", stiffness: 300, damping: 15 },
                  }}
                >
                  Dynamic Learning Path
                </motion.h1>
                <motion.p
                  className={styles.subtitle}
                  animate={{ opacity: [0.6, 1, 0.6] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                >
                  <Sparkles className="w-3 h-3 mr-1" />
                  AI-Powered Learning
                </motion.p>
              </motion.div>
            </motion.div>
          </div>

          <div className="flex items-center pr-6">
            {displayUsername ? (
              <motion.div className={styles.userControls} variants={anim.itemVariants}>
                <div className={styles.actionGroup}>
                  <div ref={panelRef} className="relative z-30">
                    <motion.button
                      onClick={() => {
                        setIsPanelOpen(prev => !prev);
                      }}
                      className={buttonStyle}
                      variants={anim.iconVariants}
                      initial="initial"
                      whileHover="hover"
                      whileTap="tap"
                    >
                      {/* MODIFICARE 3: Pictograma mărită (w-5 h-5) și culoare schimbată */}
                      <Bell className="w-[18px] h-[18px] text-slate-600 group-hover:text-purple-600 transition-colors" />
                      <AnimatePresence>
                        {unreadCount > 0 && (
                          <>
                            <motion.div
                              className="absolute -top-1 -right-1 w-4 h-4 rounded-full"
                              animate={{
                                boxShadow: [
                                  "0 0 0 0px rgba(239, 68, 68, 0.7)",
                                  "0 0 0 10px rgba(239, 68, 68, 0)",
                                ],
                              }}
                              transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "easeOut",
                              }}
                            />
                            <motion.div
                              className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-white"
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              exit={{ scale: 0 }}
                              transition={{ type: "spring", stiffness: 500, damping: 30 }}
                            >
                              <span className="text-[9px] font-bold">{unreadCount}</span>
                            </motion.div>
                          </>
                        )}
                      </AnimatePresence>
                    </motion.button>
                    <AnimatePresence>
                      {isPanelOpen && <NotificationPanel onClose={() => setIsPanelOpen(false)} />}
                    </AnimatePresence>
                  </div>
                </div>
                <UserDisplayV1 displayUsername={displayUsername} />
              </motion.div>
            ) : null}
          </div>
        </div>
      </motion.header>

        <motion.div
          className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-96 h-0.5 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent"
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        />
    </div>
  );
}