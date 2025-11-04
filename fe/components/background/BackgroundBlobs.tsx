import {motion} from "framer-motion";

export default function BackgroundBlobs() {  return (
    <>
      <motion.div
        className="absolute top-[-300px] left-[-300px] w-[800px] h-[800px] rounded-full filter blur-lg opacity-20"
        style={{ 
          background: "radial-gradient(circle, #811CD0 0%, #380A63 70%, transparent 100%)",
          willChange: "transform, opacity"
        }}
        animate={{ x: [0, 100, -50, 0], y: [0, -80, 40, 0], scale: [1, 1.2, 0.8, 1] }}
        transition={{ duration: 20, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-[-200px] right-[-200px] w-[700px] h-[700px] rounded-full filter blur-lg opacity-25"
        style={{ 
          background: "radial-gradient(circle, #CE1C5B 0%, #770F34 60%, transparent 100%)",
          willChange: "transform, opacity"
        }}
        animate={{ x: [0, -120, 60, 0], y: [0, 60, -40, 0], scale: [1, 0.9, 1.3, 1] }}
        transition={{ duration: 18, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 3 }}
      />
      <motion.div
        className="absolute top-[30%] right-[-350px] w-[900px] h-[900px] rounded-full filter blur-lg opacity-15"
        style={{ 
          background: "radial-gradient(circle, #23CCBE 0%, #00564F 50%, transparent 100%)",
          willChange: "transform, opacity"
        }}
        animate={{ x: [0, -80, 40, 0], y: [0, 30, -60, 0], scale: [1, 1.1, 0.9, 1] }}
        transition={{ duration: 22, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 6 }}
      />
      <motion.div
        className="absolute top-[60%] left-[-100px] w-[400px] h-[400px] rounded-full filter blur-lg opacity-30"
        style={{
          background: "conic-gradient(from 0deg, #ECDFFE, #811CD0, #CE1C5B, #23CCBE, #ECDFFE)",
          willChange: "transform, opacity"
        }}
        animate={{ rotate: [0, 360], scale: [1, 1.2, 1] }}
        transition={{
          rotate: { duration: 30, repeat: Number.POSITIVE_INFINITY, ease: "linear" },
          scale: { duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" },
        }}
      />
      <motion.div
        className="absolute top-[10%] left-[20%] w-[200px] h-[200px] rounded-full filter blur-lg opacity-20"
        style={{ 
          background: "radial-gradient(circle, #F8DAE5 0%, #CE1C5B 100%)",
          willChange: "transform, opacity"
        }}
        animate={{
          x: [0, 50, -30, 0],
          y: [0, -40, 20, 0],
          opacity: [0.2, 0.4, 0.1, 0.2],
        }}
        transition={{ duration: 15, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 1 }}
      />
      <motion.div
        className="absolute bottom-[20%] left-[60%] w-[300px] h-[300px] rounded-full filter blur-lg opacity-25"
        style={{ 
          background: "radial-gradient(circle, #D2F8F5 0%, #23CCBE 80%, transparent 100%)",
          willChange: "transform, opacity"
        }}
        animate={{
          x: [0, -60, 40, 0],
          y: [0, 50, -30, 0],
          scale: [1, 0.8, 1.2, 1],
        }}
        transition={{ duration: 16, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 4 }}
      />
    </>
  )
}