"use client";

import React, { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { Mail, ArrowRight, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/common/Button";
import { api } from "@/lib/api";
import { MagicLinkLoginProps, LoginState } from "@/components/auth/types";

export default function MagicLinkLogin({ onSuccess, onBack }: MagicLinkLoginProps) {
  const [state, setState] = useState<LoginState>({
    email: "",
    isLoading: false,
    isEmailSent: false,
    error: null,
    success: null
  });

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateEmail(state.email)) {
      setState(prev => ({
        ...prev,
        error: "Please enter a valid email address"
      }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      await api.sendMagicLink(state.email);

      setState(prev => ({
        ...prev,
        isLoading: false,
        isEmailSent: true,
        success: `Magic link sent to ${state.email}. Check your inbox!`
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "An unexpected error occurred"
      }));
    }
  };

    const verifyMagicLink = useCallback(async (token: string) => {
    try {
      const data = await api.verifyMagicLink(token);
      
      // Store the token in localStorage
      localStorage.setItem('auth_token', data.access_token);
      
      onSuccess(data.access_token);
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : "Failed to verify magic link"
      }));
    }
  }, [onSuccess]);
  // Check for token in URL (when user clicks magic link)
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
      verifyMagicLink(token);
    }
  }, [verifyMagicLink]);



  return (
    <motion.div
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <motion.div
          className="text-center mb-8"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <motion.div
            className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Mail className="w-8 h-8 text-white" />
          </motion.div>
          
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            Secure Login
          </h1>
          
          <p className="text-gray-600 text-sm">
            Enter your email to receive a secure login link
          </p>
        </motion.div>

        {!state.isEmailSent ? (
          <motion.form
            onSubmit={handleSendMagicLink}
            className="space-y-6"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={state.email}
                onChange={(e) => setState(prev => ({ ...prev, email: e.target.value, error: null }))}
                placeholder="yourname@example.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                disabled={state.isLoading}
                required
              />
            </div>

            {state.error && (
              <motion.div
                className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <AlertCircle className="w-5 h-5" />
                <span className="text-sm">{state.error}</span>
              </motion.div>
            )}

            <Button
              type="submit"
              disabled={state.isLoading || !state.email}
              className="w-full flex items-center justify-center space-x-2"
            >
              {state.isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
              ) : (
                <>
                  <span>Send Magic Link</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </Button>

            {onBack && (
              <Button
                type="button"
                variant="hollow"
                onClick={onBack}
                className="w-full"
              >
                Back
              </Button>
            )}
          </motion.form>
        ) : (
          <motion.div
            className="text-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <motion.div
              className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", delay: 0.3 }}
            >
              <CheckCircle className="w-8 h-8 text-white" />
            </motion.div>
            
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Check Your Email
            </h2>
            
            <p className="text-gray-600 text-sm mb-6">
              We've sent a secure login link to <br />
              <strong>{state.email}</strong>
            </p>
            
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <p className="text-blue-700 text-sm">
                📧 Click the link in your email to log in securely. The link will expire in 15 minutes.
              </p>
            </div>

            <Button
              variant="hollow"
              onClick={() => setState(prev => ({ ...prev, isEmailSent: false, email: "", success: null }))}
              className="w-full"
            >
              Try Different Email
            </Button>
          </motion.div>
        )}

        {state.success && !state.isEmailSent && (
          <motion.div
            className="mt-4 flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-lg"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm">{state.success}</span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
