import React, { createContext, useContext, useEffect, useState } from 'react';
import type { UserProfile, UserRole } from '../types';
import { authService } from '../services/authService';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  role: UserRole | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<UserProfile>;
  studentLogin: (studentName: string, studentId: string) => Promise<UserProfile>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<UserProfile>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => authService.getStoredUser());
  const [loading, setLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    if (authService.isAuthenticated()) {
      try {
        const profile = await authService.getCurrentUser();
        setUser(profile);
      } catch {
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    refreshProfile();

    const handleSessionExpired = () => {
      setUser(null);
    };

    window.addEventListener('fipp:session_expired', handleSessionExpired);
    return () => {
      window.removeEventListener('fipp:session_expired', handleSessionExpired);
    };
  }, []);

  const login = async (username: string, password: string): Promise<UserProfile> => {
    setLoading(true);
    try {
      const res = await authService.login(username, password);
      setUser(res.user);
      return res.user;
    } finally {
      setLoading(false);
    }
  };

  const studentLogin = async (studentName: string, studentId: string): Promise<UserProfile> => {
    setLoading(true);
    try {
      const res = await authService.studentLogin(studentName, studentId);
      setUser(res.user);
      return res.user;
    } finally {
      setLoading(false);
    }
  };

  const changePassword = async (currentPassword: string, newPassword: string): Promise<UserProfile> => {
    const res = await authService.changePassword(currentPassword, newPassword);
    setUser(res.user);
    return res.user;
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        role: user?.role || null,
        loading,
        login,
        studentLogin,
        changePassword,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
