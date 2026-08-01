"use client";

import { usePathname } from "next/navigation";
import { DashboardShell } from "./dashboard-shell";

export function DashboardFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const usesStandaloneLayout =
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password" ||
    pathname === "/change-password" ||
    pathname === "/verify-email" ||
    pathname.startsWith("/onboarding");

  return usesStandaloneLayout ? (
    children
  ) : (
    <DashboardShell>{children}</DashboardShell>
  );
}
