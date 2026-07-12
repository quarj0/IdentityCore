"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { PlatformSidebar } from "./platform-sidebar";
import { PlatformTopbar } from "./platform-topbar";
import { getAccessToken } from "@/lib/auth";

type PlatformAdminShellProps = {
  children: ReactNode;
};

export function PlatformAdminShell({ children }: PlatformAdminShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";
  const [ready, setReady] = useState(isLoginPage);

  useEffect(() => {
    if (isLoginPage) {
      setReady(true);
      if (getAccessToken()) {
        router.replace("/");
      }
      return;
    }

    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }

    setReady(true);
  }, [isLoginPage, router]);

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600">
        Loading platform admin...
      </main>
    );
  }

  if (isLoginPage) {
    return <div className="min-h-screen bg-slate-50 text-slate-950">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
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
