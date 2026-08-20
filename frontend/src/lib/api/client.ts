import axios from "axios";

import { tokenStore } from "./tokenStore";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = axios.create({ baseURL });

apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.getRefreshToken();
  if (!refresh) return null;

  try {
    const { data } = await axios.post<{ access: string; refresh: string }>(`${baseURL}/auth/token/refresh/`, {
      refresh,
    });
    // ROTATE_REFRESH_TOKENS=True on the backend blacklists the old refresh
    // token on every use — storing only the new access token here would
    // silently break the session on the *second* refresh.
    tokenStore.setTokens(data.access, data.refresh);
    return data.access;
  } catch {
    tokenStore.clear();
    tokenStore.notifySessionExpired();
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const url: string = originalRequest?.url ?? "";
    const isAuthBootstrapCall = url.includes("/auth/login") || url.includes("/auth/token/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthBootstrapCall) {
      originalRequest._retry = true;

      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const newAccessToken = await refreshPromise;

      if (newAccessToken) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  },
);

export { refreshAccessToken };
