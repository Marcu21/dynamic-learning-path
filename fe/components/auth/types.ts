import React from "react";

export interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

export interface MagicLinkLoginProps {
  onSuccess: (token: string) => void;
  onBack?: () => void;
}

export interface LoginState {
  email: string;
  isLoading: boolean;
  isEmailSent: boolean;
  error: string | null;
  success: string | null;
}