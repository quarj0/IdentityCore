import React from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface DashboardLayoutProps {
  children: React.ReactNode;
  breadcrumb?: { label: string; href?: string }[];
}

export function DashboardLayout({ children, breadcrumb }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen bg-transparent">
      <Sidebar />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Topbar breadcrumb={breadcrumb} />
        <main className="flex-1 px-4 pb-4 pt-2 md:px-6 md:pb-6">
          <div className="min-h-full rounded-[2rem] border border-border/70 bg-background/74 shadow-[0_28px_90px_-54px_rgba(15,23,42,0.45)] backdrop-blur-xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
