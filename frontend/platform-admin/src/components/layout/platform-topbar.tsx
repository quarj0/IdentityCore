"use client";

import { useState } from "react";
import { LogOut, Menu } from "lucide-react";
import { Button } from "@identitycore/ui";
import { useRouter } from "next/navigation";
import { logoutPlatformAdmin } from "@/lib/admin-api";

type PlatformTopbarProps = {
  onOpenNavigation: () => void;
};

export function PlatformTopbar({ onOpenNavigation }: PlatformTopbarProps) {
  const router = useRouter();
  const [logoutError, setLogoutError] = useState("");
  async function logout() {
    try {
      await logoutPlatformAdmin();
    } catch {
      setLogoutError(
        "Local credentials were cleared. Server sign-out could not be confirmed; retry before leaving this device.",
      );
      return;
    }
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-slate-950/85 backdrop-blur">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-200 lg:hidden"
          aria-label="Open navigation"
          onClick={onOpenNavigation}
        >
          <Menu className="size-5" aria-hidden="true" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="ml-auto text-slate-300"
          aria-label="Sign out"
          onClick={logout}
        >
          <LogOut className="size-5" aria-hidden="true" />
        </Button>

        {logoutError ? (
          <p role="alert" className="text-sm text-red-200">
            {logoutError}
          </p>
        ) : null}
        <div className="flex size-9 items-center justify-center rounded-full bg-cyan-300 text-sm font-bold text-slate-950">
          IC
        </div>
      </div>
    </header>
  );
}
