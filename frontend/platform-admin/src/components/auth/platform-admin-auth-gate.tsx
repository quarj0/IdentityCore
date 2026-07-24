"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@identitycore/ui";
import { getCurrentPlatformUser } from "@/lib/admin-api";

type PlatformAdminAuthGateProps = {
  children: ReactNode;
};

export function PlatformAdminAuthGate({ children }: PlatformAdminAuthGateProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [state, setState] = useState<"checking" | "authorized" | "denied">("checking");

  useEffect(() => {
    if (pathname === "/login") {
      return;
    }

    let active = true;
    void getCurrentPlatformUser()
      .then((user) => {
        if (!active) return;
        if (user.is_platform_admin) {
          setState("authorized");
          return;
        }
        setState("denied");
      })
      .catch(() => {
        if (active) router.replace("/login");
      });

    return () => {
      active = false;
    };
  }, [pathname, router]);

  if (pathname === "/login" || state === "authorized") return <>{children}</>;

  if (state === "denied") {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <section className="max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-slate-950">Platform access required</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Your account is authenticated but is not authorized to access the Platform Admin console.
          </p>
          <Button className="mt-6" onClick={() => router.replace("/login")}>
            Use another account
          </Button>
        </section>
      </main>
    );
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50" aria-busy="true">
      <p className="text-sm text-slate-600">Verifying platform access…</p>
    </main>
  );
}
