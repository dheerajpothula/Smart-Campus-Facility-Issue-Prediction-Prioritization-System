import { api, TokenManager } from './apiClient';
import type { AuthResponse, UserProfile } from '../types';

export const authService = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const data = await api.post<AuthResponse>('/api/auth/login', { username, password });
    TokenManager.setSession(data.access_token, data.refresh_token, data.user);
    return data;
  },

  studentLogin: async (studentName: string, studentId: string): Promise<AuthResponse> => {
    const data = await api.post<AuthResponse>('/api/auth/student/login', {
      student_name: studentName,
      student_id: studentId,
    });
    TokenManager.setSession(data.access_token, data.refresh_token, data.user);
    return data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<AuthResponse> => {
    const data = await api.post<AuthResponse>('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    TokenManager.setSession(data.access_token, data.refresh_token, data.user);
    return data;
  },

  getCurrentUser: async (): Promise<UserProfile> => {
    const res = await api.get<{ success: boolean; user: UserProfile }>('/api/auth/me');
    return res.user;
  },

  logout: async (): Promise<void> => {
    try {
      const refreshToken = TokenManager.getRefreshToken();
      await api.post('/api/auth/logout', refreshToken ? { refresh_token: refreshToken } : undefined);
    } catch {
      // Backend token revocation attempt, clear locally regardless
    } finally {
      TokenManager.clearSession();
    }
  },

  getStoredUser: (): UserProfile | null => {
    return TokenManager.getUser();
  },

  isAuthenticated: (): boolean => {
    return !!TokenManager.getAccessToken();
  },
};
