import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "lib/api";
import type { SessionState } from "types/api";

interface AuthContextValue {
  session: SessionState | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<SessionState | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    const state = await api.get<SessionState>("/api/admin/auth/me");
    setSession(state);
  };

  const logout = async () => {
    await api.post("/api/admin/auth/logout");
    setSession({ authenticated: false, must_change_password: false, user: null });
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      session,
      loading,
      refresh,
      logout
    }),
    [loading, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
