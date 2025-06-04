'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  sub: string;
  email: string;
  name: string;
  provider: string;
  agent: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => void;
  validateToken: (token: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token in localStorage when component mounts
    const checkExistingAuth = async () => {
      try {
        console.log('🔧 Checking for existing authentication...');
        
        if (typeof window === 'undefined') {
          console.log('❌ Server side detected, skipping auth check');
          setIsLoading(false);
          return;
        }

        const token = localStorage.getItem('auth_token');
        if (token) {
          console.log('🎫 Existing token found, validating...');
          await validateToken(token);
        } else {
          console.log('📭 No existing token found');
          setIsLoading(false);
        }
      } catch (error) {
        console.error('❌ Error checking existing auth:', error);
        setIsLoading(false);
      }
    };

    checkExistingAuth();
  }, []);

  const login = async () => {
    console.log('🚀 Login button clicked!');
    
    try {
      console.log('📝 Setting loading state...');
      setIsLoading(true);
      
      console.log('🔐 Calling server-side login API...');
      
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          callbackUrl: `${window.location.origin}/auth/callback`
        }),
      });

      const loginResponse = await response.json();
      console.log('📋 Login response:', loginResponse);

      if (loginResponse.success && loginResponse.redirectUrl) {
        console.log('✅ Login successful, redirecting to:', loginResponse.redirectUrl);
        // Store state for validation after callback
        localStorage.setItem('auth_state', loginResponse.state);
        // Redirect to Google OAuth
        window.location.href = loginResponse.redirectUrl;
      } else {
        console.error('❌ Login failed:', loginResponse);
        alert('Login failed: ' + (loginResponse.error || loginResponse.message || 'Unknown error'));
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      alert('Login error: ' + (error as Error).message);
      setIsLoading(false);
    }
  };

  const validateToken = async (token: string): Promise<boolean> => {
    try {
      console.log('🔍 Validating token via API...');
      
      const response = await fetch('/api/auth/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const validationResult = await response.json();
      
      if (validationResult.success && validationResult.valid && validationResult.user) {
        console.log('✅ Token valid, user:', validationResult.user);
        setUser(validationResult.user);
        localStorage.setItem('auth_token', token);
        setIsLoading(false);
        return true;
      } else {
        console.log('❌ Token invalid, removing...');
        // Token is invalid, remove it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_state');
        setUser(null);
        setIsLoading(false);
        return false;
      }
    } catch (error) {
      console.error('❌ Token validation error:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_state');
      setUser(null);
      setIsLoading(false);
      return false;
    }
  };

  const logout = () => {
    console.log('👋 Logging out...');
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_state');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    validateToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 