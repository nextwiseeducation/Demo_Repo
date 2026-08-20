const REFRESH_KEY = "nextwise_refresh_token";

let accessToken: string | null = null;
const sessionExpiredListeners = new Set<() => void>();

/**
 * Access token lives in memory only (never persisted — 30 min lifetime,
 * losing it on refresh/tab-close is intentional). Refresh token lives in
 * localStorage since there's no cookie-based refresh flow on the backend
 * to use instead, and its 14-day lifetime implies "stay logged in" is the
 * intended UX. SIMPLE_JWT rotates the refresh token on every use, so
 * setTokens() must always be called with both, never the access token alone.
 */
export const tokenStore = {
  getAccessToken: () => accessToken,

  getRefreshToken: () => localStorage.getItem(REFRESH_KEY),

  setTokens: (access: string, refresh: string) => {
    accessToken = access;
    localStorage.setItem(REFRESH_KEY, refresh);
  },

  clear: () => {
    accessToken = null;
    localStorage.removeItem(REFRESH_KEY);
  },

  onSessionExpired: (listener: () => void) => {
    sessionExpiredListeners.add(listener);
    return () => {
      sessionExpiredListeners.delete(listener);
    };
  },

  notifySessionExpired: () => {
    for (const listener of sessionExpiredListeners) listener();
  },
};
