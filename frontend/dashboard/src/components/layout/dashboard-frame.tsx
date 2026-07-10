"use client";

import { usePathname } from "next/navigation";
import { DashboardShell } from "./dashboard-shell";

export function DashboardFrame({ children }: { children: React.ReactNode }) {
  return usePathname() === "/login" ? children : <DashboardShell>{children}</DashboardShell>;
}
