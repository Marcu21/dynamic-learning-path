import {api} from './api';
import {AuthState, AuthUser} from '@/lib/types';

class AuthenticationService {
  private listeners: ((state: AuthState) => void)[] = [];
  private state: AuthState = {
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true
  };

  constructor() {
    this.initializeAuth();
  }

  // Initialize authentication state from localStorage
  private async initializeAuth() {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
      this.state.token = token;
      try {
        await this.validateAndSetUser();
      } catch (error) {
        this.clearAuth();
      }
    }
    
    this.state.isLoading = false;
    this.notifyListeners();
  }

  // Validate token and set user
  private async validateAndSetUser() {
    try {
      const validationResult = await api.validateToken();
      if (validationResult.valid) {
        this.state.user = await api.getCurrentUser();
        this.state.isAuthenticated = true;
      } else {
        this.clearAuth();
      }
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }

  // Clear authentication data
  private clearAuth() {
    localStorage.removeItem('auth_token');
    this.state = {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    };
  }

  // Notify all listeners of state changes
  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.state));
  }

  // Subscribe to auth state changes
  subscribe(listener: (state: AuthState) => void) {
    this.listeners.push(listener);
    // Immediately call with current state
    listener(this.state);
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  // Login with magic link token
  async login(token: string): Promise<AuthUser> {
    this.state.isLoading = true;
    this.notifyListeners();

    try {
      // Store token
      localStorage.setItem('auth_token', token);
      this.state.token = token;

      // Get user info
      const user = await api.getCurrentUser();
      this.state.user = user;
      this.state.isAuthenticated = true;
      this.state.isLoading = false;

      this.notifyListeners();
      return user;
    } catch (error) {
      this.clearAuth();
      this.state.isLoading = false;
      this.notifyListeners();
      throw error;
    }
  }

  // Logout
  async logout() {
    try {
      // Call backend logout endpoint
      await api.logout();
    } catch (error) {
    } finally {
      this.clearAuth();
      this.notifyListeners();
    }
  }
}

// Create singleton instance
export const authService = new AuthenticationService();