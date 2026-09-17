import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiFetch, clearTokens, getStoredTokens, setUnauthorizedHandler, storeTokens } from "./api-client";

type User = { id: string; email: string };

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));
    (async () => {
      const { accessToken } = await getStoredTokens();
      if (accessToken) {
        try {
          setUser(await fetchCurrentUser());
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    await storeTokens(tokens.access_token, tokens.refresh_token);
    setUser(await fetchCurrentUser());
  };

  const register = async (email: string, password: string) => {
    await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    await login(email, password);
  };

  const logout = async () => {
    await clearTokens();
    setUser(null);
  };

  const value = useMemo(() => ({ user, isLoading, login, register, logout }), [user, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
