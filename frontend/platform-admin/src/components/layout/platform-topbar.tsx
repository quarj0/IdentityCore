"use client";

import { Bell, Command, LogOut, Menu, Search } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { useRouter } from "next/navigation";
import { logoutPlatformAdmin } from "@/lib/admin-api";

export function PlatformTopbar() {
  const router = useRouter();
  async function logout() {
    try {
      await logoutPlatformAdmin();
    } finally {
      router.replace("/login");
    }
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-slate-950/85 backdrop-blur">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-200 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" aria-hidden="true" />
        </Button>

        <div className="relative hidden flex-1 md:block">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500"
            aria-hidden="true"
          />

          <Input
            placeholder="Search organizations, verifications, tickets, audits..."
            className="h-10 max-w-2xl border-slate-200 bg-white/5 pl-10 text-slate-100 placeholder:text-slate-500"
            aria-label="Search platform admin"
          />
        </div>

        <Button
          variant="outline"
          className="ml-auto hidden border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10 md:inline-flex"
        >
          <Command className="mr-2 size-4" aria-hidden="true" />
          Command
          <kbd className="ml-2 rounded border border-slate-200 bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-400">
            ⌘K
          </kbd>
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="text-slate-300"
          aria-label="View notifications"
        >
          <Bell className="size-5" aria-hidden="true" />
        </Button>

        <Button variant="ghost" size="icon" className="text-slate-300" aria-label="Sign out" onClick={logout}>
          <LogOut className="size-5" aria-hidden="true" />
        </Button>

        <div className="flex size-9 items-center justify-center rounded-full bg-cyan-300 text-sm font-bold text-slate-950">
          IC
        </div>
      </div>
    </header>
  );
}
