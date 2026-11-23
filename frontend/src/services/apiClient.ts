/**
 * FIPP 2.0 — Centralized HTTP API Client.
 * Handles automatic JWT Bearer injection, token refreshing, and error normalization.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class TokenManager {
  private static ACCESS_TOKEN_KEY = 'fipp_access_token';
  private static REFRESH_TOKEN_KEY = 'fipp_refresh_token';
  private static USER_KEY = 'fipp_user_profile';

  static getAccessToken(): string | null {
    return sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static getRefreshToken(): string | null {
    return sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static getUser(): any | null {
    const raw = sessionStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  static setSession(accessToken: string, refreshToken?: string, user?: any) {
    sessionStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      // Stored in sessionStorage (isolated to browser tab session, cleared upon close)
      sessionStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    }
    if (user) {
      sessionStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
  }

  static clearSession() {
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
  }
}

export { TokenManager };

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const token = TokenManager.getAccessToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token && !(headers as Record<string, string>)['Authorization']) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  try {
    let response = await fetch(url, { ...options, headers });

    // Handle token expiration & automatic refresh
    if (response.status === 401 && !endpoint.includes('/api/auth/login') && !endpoint.includes('/api/auth/refresh')) {
      const refreshToken = TokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const refreshRes = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const refreshData = await refreshRes.json();
            TokenManager.setSession(refreshData.access_token);
            // Retry original request with fresh token
            (headers as Record<string, string>)['Authorization'] = `Bearer ${refreshData.access_token}`;
            response = await fetch(url, { ...options, headers });
          } else {
            TokenManager.clearSession();
            window.dispatchEvent(new CustomEvent('fipp:session_expired'));
          }
        } catch {
          TokenManager.clearSession();
          window.dispatchEvent(new CustomEvent('fipp:session_expired'));
        }
      } else {
        TokenManager.clearSession();
        window.dispatchEvent(new CustomEvent('fipp:session_expired'));
      }
    }

    if (!response.ok) {
      let errorDetail: any = null;
      try {
        errorDetail = await response.json();
      } catch {
        errorDetail = await response.text();
      }

      const message =
        (typeof errorDetail === 'object' && (errorDetail?.detail || errorDetail?.message)) ||
        `Request failed with status ${response.status}`;

      const err: ApiError = {
        status: response.status,
        message: typeof message === 'string' ? message : JSON.stringify(message),
        detail: errorDetail,
      };
      throw err;
    }

    // Check if JSON response
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    }
    return (await response.text()) as unknown as T;
  } catch (error: any) {
    if (error.status && error.message) {
      throw error;
    }
    throw {
      status: 0,
      message: error.message || 'Network connection failed. Verify that the backend is running.',
      detail: error,
    } as ApiError;
  }
}

export const api = {
  get: <T>(url: string, options?: RequestInit) =>
    request<T>(url, { method: 'GET', ...options }),

  post: <T>(url: string, body?: any, options?: RequestInit) =>
    request<T>(url, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),

  patch: <T>(url: string, body?: any, options?: RequestInit) =>
    request<T>(url, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),

  upload: async <T>(url: string, file: File): Promise<T> => {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    const token = TokenManager.getAccessToken();
    const formData = new FormData();
    formData.append('file', file);

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(fullUrl, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw {
        status: response.status,
        message: err.detail || 'Photo upload failed',
      };
    }
    return response.json();
  },
};
