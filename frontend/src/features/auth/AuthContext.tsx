import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { toast } from "sonner";

import * as authApi from "@/lib/api/auth";
import { refreshAccessToken } from "@/lib/api/client";
import { tokenStore } from "@/lib/api/tokenStore";
import type { Me } from "@/types/api";

interface AuthContextValue {
  user: Me | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!tokenStore.getRefreshToken()) {
        setIsBootstrapping(false);
        return;
      }
      const access = await refreshAccessToken();
      if (cancelled) return;
      if (!access) {
        setIsBootstrapping(false);
        return;
      }
      try {
        const me = await authApi.getMe();
        if (!cancelled) setUser(me);
      } catch {
        tokenStore.clear();
      } finally {
        if (!cancelled) setIsBootstrapping(false);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return tokenStore.onSessionExpired(() => {
      setUser(null);
      toast.error("Your session expired. Please log in again.");
    });
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authApi.login({ email, password });
    tokenStore.setTokens(tokens.access, tokens.refresh);
    const me = await authApi.getMe();
    setUser(me);
  }

  async function logout() {
    const refresh = tokenStore.getRefreshToken();
    tokenStore.clear();
    setUser(null);
    if (refresh) {
      // Best-effort — a failed logout call must never trap the user in a
      // "logged in" UI, local state is already cleared above regardless.
      authApi.logout(refresh).catch(() => {});
    }
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: user !== null, isBootstrapping, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
