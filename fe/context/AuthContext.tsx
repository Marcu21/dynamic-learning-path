'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { AuthContextType, AuthProviderProps } from '@/context/types';
import { User } from '@/types/user';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;
  
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      
      if (storedToken) {
        setToken(storedToken);
        try {
          const isValid = await validateAuth();
          if (!isValid) {
            logout();
          }
        } catch (error) {
          logout();
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);
  
  const login = async (newToken: string) => {
    setIsLoading(true);
    try {
      localStorage.setItem('auth_token', newToken);
      setToken(newToken);
      
      const userData = await api.getCurrentUser();
      setUser(userData);
      
      localStorage.setItem('currentUserId', userData.id);
      localStorage.setItem('currentUsername', userData.username);
    } catch (error) {
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout().catch(() => {});
  
    // Clear all local authentication data.
    localStorage.removeItem('auth_token');
    localStorage.removeItem('currentUserId');
    localStorage.removeItem('currentUsername');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (!token) return;
    
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
      
      localStorage.setItem('currentUserId', userData.id);
      localStorage.setItem('currentUsername', userData.username);
    } catch (error) {
      if (error instanceof Error && error.message.includes('Authentication required')) {
        logout();
      }
      throw error;
    }
  };

  const validateAuth = async (): Promise<boolean> => {
    const currentToken = localStorage.getItem('auth_token');
    if (!currentToken) {
        return false;
    }
    try {
        const validationResult = await api.validateToken();
        if (validationResult.valid) {
            // Only fetch user data if we don't have it yet
            if (!user) {
                const userData = await api.getCurrentUser();
                setUser(userData);
                localStorage.setItem('currentUserId', userData.id);
                localStorage.setItem('currentUsername', userData.username);
            }
            return true;
        } else {
            logout();
            return false;
        }
    } catch (error: any) {
        if (error?.response?.status === 401 || error?.response?.status === 403) {
            logout();
        }
        return false;
    }
  };

  const value: AuthContextType = {
    user, token, isLoading, isAuthenticated,
    login, logout, refreshUser, validateAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};