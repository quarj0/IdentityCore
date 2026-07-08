import type { ReactNode } from "react";
import { DashboardSidebar } from "./dashboard-sidebar";
import { DashboardTopbar } from "./dashboard-topbar";
import { MobileSidebar } from "./mobile-sidebar";
import { CommandPalette } from "../search/command-palette";

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div className="grid lg:grid-cols-[288px_1fr]">
        <DashboardSidebar />

        <div className="min-w-0">
          <div className="lg:hidden">
            <div className="flex h-16 items-center border-b border-slate-200 bg-white px-4">
              <MobileSidebar />
              <p className="ml-3 text-sm font-semibold">IdentityCore</p>
            </div>
          </div>

          <DashboardTopbar />
          <CommandPalette />

          <main id="main-content" className="px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
