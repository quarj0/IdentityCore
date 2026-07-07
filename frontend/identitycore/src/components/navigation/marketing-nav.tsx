"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { BrandMark, Button } from "@identitycore/ui";
import { NAV_GROUPS } from "./nav-data";
import { NavFlyout } from "./nav-flyout";
import { MobileNav } from "./mobile-nav";

export interface MarketingNavProps {
  activePath?: string;
}

export function MarketingNav({ activePath }: MarketingNavProps) {
  const [menuOpen, setMenuOpen] = useState(false);

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
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>

          <Button asChild size="sm" className="rounded-xl">
            <Link href="/register">Create workspace</Link>
          </Button>
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
        />
      ) : null}
    </header>
  );
}
