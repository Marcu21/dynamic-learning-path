"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUp, Info } from "lucide-react";
import Link from "next/link";
import * as anim from "./animations";
import * as styles from "./styles";

type Particle = { left: number; top: number };

export default function Footer() {
  const [, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    setParticles(
      Array.from({ length: 15 }, () => ({
        left: Math.random() * 100,
        top: Math.random() * 100,
      }))
    );
  }, []);

  const scrollToTop = () =>
    window.scrollTo({ top: 0, behavior: "smooth" });

  return (
    <div className={styles.wrapper}>
      <div className={styles.bgBlobsWrapper}>
        {/* gradient blobs */}
        <motion.div
          className="absolute -top-40 -left-40 w-80 h-80 rounded-full filter blur-3xl opacity-20 mix-blend-multiply"
          style={{ background: "linear-gradient(45deg, #667eea, #764ba2)" }}
          animate={{
            x: [0, 50, -30, 0],
            y: [0, -20, 30, 0],
            scale: [1, 1.2, 0.8, 1],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full filter blur-2xl opacity-25 mix-blend-multiply"
          style={{ background: "linear-gradient(135deg, #ffecd2, #fcb69f)" }}
          animate={{
            x: [0, -60, 40, 0],
            y: [0, 40, -20, 0],
            scale: [1, 0.7, 1.3, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2,
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full filter blur-3xl opacity-15 mix-blend-multiply"
          style={{ background: "linear-gradient(225deg, #a8edea, #fed6e3)" }}
          animate={{ rotate: [0, 360], scale: [1, 1.4, 1] }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 4,
          }}
        />
      </div>

      <motion.footer
        className={styles.footerBase}
        initial="hidden"
        animate="visible"
        variants={anim.footerVariants}
      >
        <div className={styles.container}>
            <div className="py-4">
              <div className="flex justify-center text-center border-b border-white/10">
                <motion.p className={styles.copyText} animate={{ opacity: [0.7,1,0.7] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}>
                  © 2025 Dynamic Learning Path. Made with{" "}
                  <motion.span animate={{ scale:[1,1.2,1], color:["#ef4444","#f97316","#ef4444"] }} transition={{ duration:2, repeat:Infinity, ease:"easeInOut" }}>
                    ❤️
                  </motion.span>{" "}
                  and too much coffee
                </motion.p>
              </div>

              {/* Rândul 2: Butoane aliniate */}
              <div className="flex justify-between items-center">
                {/* Butonul 'About' în stânga */}
                <Link href="/about" legacyBehavior>
                  <motion.a
                    className={styles.btn}
                    variants={anim.linkVariants}
                    initial="initial"
                    whileHover="hover"
                    whileTap="tap"
                  >
                    <Info className="w-4 h-4" />
                    <span className="text-sm font-sans ml-2">About</span>
                  </motion.a>
                </Link>

                <motion.button
                  onClick={scrollToTop}
                  className={styles.btn}
                  variants={anim.linkVariants}
                  initial="initial"
                  whileHover="hover"
                  whileTap="tap"
                >
                  <span className="text-sm font-sans">Back to top</span>
                  <motion.div animate={{ y:[0,-2,0] }} transition={{ duration:2, repeat:Infinity, ease:"easeInOut" }}>
                    <ArrowUp className="w-4 h-4 ml-2" />
                  </motion.div>
                </motion.button>
              </div>
            </div>
        </div>
      </motion.footer>
    </div>
  );
}