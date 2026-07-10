"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { backend } from "@/lib/backend";

type DashboardUser = { id?: string; email: string; full_name?: string };
type SessionContextValue = {
  user: DashboardUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function DashboardSession({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<DashboardUser | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const publicRoute = pathname === "/login";

  useEffect(() => {
    backend.restoreSession()
      .then(() => backend.me<DashboardUser>())
      .then((payload) => setUser(payload.user))
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (ready && !user && !publicRoute) router.replace("/login");
    if (ready && user && publicRoute) router.replace("/");
  }, [publicRoute, ready, router, user]);

  async function login(email: string, password: string) {
    const payload = await backend.login(email, password);
    setUser(payload.user as DashboardUser);
    router.replace("/");
  }

  async function logout() {
    await backend.logout();
    setUser(null);
    router.replace("/login");
  }

  if (!ready && !publicRoute) {
    return <div className="flex min-h-screen items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>;
  }

  return <SessionContext.Provider value={{ user, login, logout }}>{children}</SessionContext.Provider>;
}

export function useDashboardSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("Dashboard session is unavailable.");
  return value;
}
