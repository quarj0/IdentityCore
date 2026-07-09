import type { ReactNode } from "react";
import { PlatformSidebar } from "@/components/layout/platform-sidebar";
import { PlatformTopbar } from "@/components/layout/platform-topbar";

type PlatformAdminShellProps = {
  children: ReactNode;
};

export function PlatformAdminShell({ children }: PlatformAdminShellProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <PlatformSidebar />

      <div className="min-h-screen lg:pl-72">
        <PlatformTopbar />

        <main className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}