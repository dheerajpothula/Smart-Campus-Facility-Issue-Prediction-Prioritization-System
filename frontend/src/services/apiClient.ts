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
    sessionStorage.removeItem('fipp_student_agreed');
    sessionStorage.removeItem('fipp_query_draft');
  }
}

export { TokenManager };

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
}

/**
 * Consumes a Fetch Response body stream exactly once via `response.text()`,
 * safely parses JSON if present, and avoids ever calling `.json()` and `.text()`
 * separately on the same Response object.
 */
async function readResponseSafely(
  response: Response
): Promise<{ parsed: any; hasJson: boolean; rawText: string }> {
  const rawText = await response.text();
  if (!rawText || !rawText.trim()) {
    return { parsed: null, hasJson: false, rawText: '' };
  }
  try {
    return { parsed: JSON.parse(rawText), hasJson: true, rawText };
  } catch {
    return { parsed: null, hasJson: false, rawText };
  }
}

function formatHttpErrorMessage(status: number, parsed: any, rawText: string): string {
  if (parsed && typeof parsed === 'object') {
    const rawDetail = parsed.detail ?? parsed.message ?? parsed.error;
    if (typeof rawDetail === 'string' && rawDetail.trim()) {
      return rawDetail.trim();
    }
    if (Array.isArray(rawDetail) && rawDetail.length > 0) {
      const msgs = rawDetail
        .map((item: any) => (typeof item?.msg === 'string' ? item.msg : JSON.stringify(item)))
        .filter(Boolean);
      if (msgs.length > 0) {
        return msgs.join('; ');
      }
    }
    if (rawDetail !== undefined && rawDetail !== null) {
      return JSON.stringify(rawDetail);
    }
  }
  const trimmed = rawText.trim();
  if (trimmed) {
    if (trimmed.startsWith('<') || /<\/?[a-z][\s\S]*>/i.test(trimmed)) {
      return `Backend service error (HTTP ${status}). Verify the API server is running and try again.`;
    }
    return trimmed;
  }
  return `Request failed with HTTP status ${status}.`;
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
    if (
      response.status === 401 &&
      !endpoint.includes('/api/auth/login') &&
      !endpoint.includes('/api/auth/student/login') &&
      !endpoint.includes('/api/auth/refresh')
    ) {
      const refreshToken = TokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const refreshRes = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          const { parsed: refreshData, hasJson: refreshHasJson } = await readResponseSafely(refreshRes);
          if (refreshRes.ok && refreshHasJson && refreshData?.access_token) {
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

    const { parsed, hasJson, rawText } = await readResponseSafely(response);

    if (!response.ok) {
      const err: ApiError = {
        status: response.status,
        message: formatHttpErrorMessage(response.status, parsed, rawText),
        detail: hasJson ? parsed : rawText || null,
      };
      throw err;
    }

    if (hasJson) {
      return parsed as T;
    }
    return rawText as unknown as T;
  } catch (error: any) {
    if (typeof error?.status === 'number' && error.status > 0 && error?.message) {
      throw error;
    }
    throw {
      status: 0,
      message: error?.message || 'Network connection failed. Verify that the backend is running.',
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

  put: <T>(url: string, body?: any, options?: RequestInit) =>
    request<T>(url, {
      method: 'PUT',
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

    const { parsed, hasJson, rawText } = await readResponseSafely(response);
    if (!response.ok) {
      throw {
        status: response.status,
        message: formatHttpErrorMessage(response.status, parsed, rawText) || 'Photo upload failed',
        detail: hasJson ? parsed : rawText || null,
      } as ApiError;
    }
    if (hasJson) {
      return parsed as T;
    }
    return rawText as unknown as T;
  },
};
