import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api } from "./api";
import type { User, UserRole } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (identifier: string, password: string) => Promise<User>;
  register: (input: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    role: UserRole;
  }) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await api.get<User | null>("/api/auth/me");
      setUser(me ?? null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const login = useCallback(async (identifier: string, password: string) => {
    const u = await api.post<User>("/api/auth/login", { identifier, password });
    setUser(u);
    return u;
  }, []);

  const register = useCallback(
    async (input: {
      username: string;
      email: string;
      password: string;
      password_confirm: string;
      role: UserRole;
    }) => {
      const u = await api.post<User>("/api/auth/register", input);
      setUser(u);
      return u;
    },
    [],
  );

  const logout = useCallback(async () => {
    await api.post("/api/auth/logout");
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, refresh, login, register, logout }),
    [user, loading, refresh, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

export function homeForRole(role: UserRole): string {
  if (role === "admin") return "/admin";
  if (role === "seller") return "/seller";
  return "/account";
}
