import { motion } from "framer-motion";
import {
  AlertTriangle,
  RefreshCw,
  Home,
  ArrowLeft,
  Server,
} from "lucide-react";
import React from "react";
import Link from 'next/link';
import type { NextPageContext } from 'next';

interface ErrorPageProps {
  statusCode?: number;
  message?: string;
}

function ServerError({ statusCode, message }: ErrorPageProps) {
  const fadeSlide = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
  } as const;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-orange-900 flex items-center justify-center p-4">
      <motion.div
        className="max-w-lg w-full text-center relative z-10"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.2 } } }}
      >
        <motion.div
          className="inline-flex items-center justify-center w-28 h-28 bg-gradient-to-br from-red-600 to-orange-700 text-white rounded-full mb-8"
          variants={fadeSlide}
        >
          <Server className="w-14 h-14" />
        </motion.div>
        <motion.h1 className="text-5xl font-bold text-white mb-4" variants={fadeSlide}>
          {statusCode}
        </motion.h1>
        <motion.h2 className="text-2xl font-semibold text-red-200 mb-6" variants={fadeSlide}>
          Server Error
        </motion.h2>
        <motion.p className="text-red-100/80 mb-8" variants={fadeSlide}>
          {message || "We're experiencing some technical difficulties on our servers. Our team has been notified."}
        </motion.p>

        <motion.div variants={fadeSlide}>
          <Link href="/" passHref>
            <motion.button
              className="w-full bg-gradient-to-r from-blue-600 to-purple-700 text-white py-4 rounded-xl font-semibold"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <Home className="w-5 h-5 inline-block mr-2" />
              <span>Go to Homepage</span>
            </motion.button>
          </Link>
          <motion.button
            onClick={() => window.location.reload()}
            className="w-full bg-white/10 text-white py-4 rounded-xl font-semibold border border-white/20 mt-4"
            whileHover={{ scale: 1.02, y: -2 }}
          >
            <RefreshCw className="w-5 h-5 inline-block mr-2" />
            Retry
          </motion.button>
        </motion.div>
      </motion.div>
    </div>
  );
}

function ClientError({ statusCode, message }: ErrorPageProps) {
    const fadeSlide = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
  } as const;

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <motion.div
        className="max-w-md w-full text-center relative z-10"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.2 } } }}
      >
        <motion.div
          className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-red-500 to-orange-600 text-white rounded-full mb-8"
          variants={fadeSlide}
        >
          <AlertTriangle className="w-12 h-12" />
        </motion.div>
        <motion.h1 className="text-4xl font-bold text-gray-800 mb-4" variants={fadeSlide}>
          {statusCode === 404 ? "Resource Not Found" : "Oops! Something went wrong"}
        </motion.h1>
        <motion.p className="text-gray-600 mb-8" variants={fadeSlide}>
          {message || "An unexpected error occurred. Don't worry, we're working on it!"}
        </motion.p>

        <motion.div className="space-y-4" variants={fadeSlide}>
            <Link href="/dashboard" passHref>
                <motion.button
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-xl font-semibold"
                    whileHover={{ scale: 1.02, y: -2 }}
                >
                    <Home className="w-4 h-4 inline-block mr-2" />
                    <span>Go to Dashboard</span>
                </motion.button>
            </Link>

            <motion.button
                onClick={() => window.history.back()}
                className="w-full bg-white text-gray-700 py-3 rounded-xl font-semibold border mt-4"
                whileHover={{ scale: 1.02, y: -2 }}
            >
                <ArrowLeft className="w-5 h-5 inline-block mr-2" />
                Go Back
            </motion.button>
        </motion.div>
      </motion.div>
    </div>
  );
}

function ErrorPage({ statusCode, message }: ErrorPageProps) {
  if (statusCode && statusCode >= 500) {
    return <ServerError statusCode={statusCode} message={message} />;
  }
  return <ClientError statusCode={statusCode} message={message} />;
}

ErrorPage.getInitialProps = ({ res, err, query }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  const message = typeof query.message === 'string' ? query.message : undefined;
  return { statusCode, message };
};

export default ErrorPage;