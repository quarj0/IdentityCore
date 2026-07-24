"use client";

import { useState, type ReactNode } from "react";
import { PlatformSidebar } from "./platform-sidebar";
import { PlatformTopbar } from "./platform-topbar";
import { usePathname } from "next/navigation";

type PlatformAdminShellProps = {
  children: ReactNode;
};

export function PlatformAdminShell({ children }: PlatformAdminShellProps) {
  const pathname = usePathname();
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);
  if (pathname === "/login") return <>{children}</>;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <PlatformSidebar />
      {mobileNavigationOpen ? (
        <>
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
            onClick={() => setMobileNavigationOpen(false)}
          />
          <PlatformSidebar mobile onNavigate={() => setMobileNavigationOpen(false)} />
        </>
      ) : null}

      <div className="min-h-screen lg:pl-72">
        <PlatformTopbar onOpenNavigation={() => setMobileNavigationOpen(true)} />

        <main className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
