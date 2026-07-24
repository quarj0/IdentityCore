"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, Settings, X } from "lucide-react";
import {
  BrandMark,
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@identitycore/ui";
import {
  AUTH_SESSION_CHANGED_EVENT,
  clearAuthSession,
  getCurrentAuthUser,
  type AuthUser,
} from "@/lib/auth";
import { NAV_GROUPS } from "./nav-data";
import { NavFlyout } from "./nav-flyout";
import { MobileNav } from "./mobile-nav";

export interface MarketingNavProps {
  activePath?: string;
}

export function MarketingNav({ activePath }: MarketingNavProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const syncAuthState = () => setUser(getCurrentAuthUser());

    syncAuthState();
    window.addEventListener(AUTH_SESSION_CHANGED_EVENT, syncAuthState);
    window.addEventListener("storage", syncAuthState);
    return () => {
      window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, syncAuthState);
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center px-4 sm:px-6">
        <Link
          href="/"
          aria-label="IdentityCore home"
          onClick={closeMenu}
          className="shrink-0"
        >
          <BrandMark subtitle="Digital identity infrastructure" />
        </Link>

        <nav
          aria-label="Primary navigation"
          className="ml-10 hidden items-center gap-1 md:flex"
        >
          {NAV_GROUPS.map((group) => (
            <NavFlyout key={group.label} group={group} activePath={activePath} />
          ))}
        </nav>

        <div className="ml-auto hidden items-center gap-2 md:flex">
          {user ? (
            <AuthenticatedActions user={user} />
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Sign in</Link>
              </Button>

              <Button asChild size="sm" className="rounded-xl">
                <Link href="/register">Create workspace</Link>
              </Button>
            </>
          )}
        </div>

        <button
          type="button"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="mobile-marketing-menu"
          onClick={() => setMenuOpen((open) => !open)}
          className="ml-auto inline-flex size-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
        >
          {menuOpen ? (
            <X className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Menu className="h-5 w-5" aria-hidden="true" />
          )}
        </button>
      </div>

      {menuOpen ? (
        <MobileNav
          groups={NAV_GROUPS}
          onNavigate={closeMenu}
          activePath={activePath}
          user={user}
        />
      ) : null}
    </header>
  );
}

function AuthenticatedActions({ user }: { user: AuthUser }) {
  const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
  const initials = displayName
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <>
      <Button asChild size="sm" className="rounded-xl">
        <Link href="/onboarding">Workspace setup</Link>
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            aria-label="Open account menu"
            className="flex items-center gap-2 rounded-xl border border-border bg-background py-1.5 pl-2 pr-3 text-left transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span className="flex size-7 items-center justify-center rounded-lg bg-slate-900 text-[11px] font-semibold text-white">
              {initials}
            </span>
            <span className="max-w-36 truncate text-sm font-medium">{displayName}</span>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-64" sideOffset={8}>
          <DropdownMenuLabel className="normal-case tracking-normal">
            <span className="block truncate text-sm font-semibold text-foreground">{displayName}</span>
            <span className="mt-0.5 block truncate text-xs font-normal text-muted-foreground">{user.email}</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/onboarding" className="flex items-center gap-2">
              <Settings className="h-4 w-4 text-muted-foreground" />
              Workspace setup
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-red-700 focus:bg-red-50 focus:text-red-700"
            onSelect={() => {
              clearAuthSession();
              window.location.assign("/");
            }}
          >
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}
