"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import Link from "next/link";
import { BrandMark, Button, Separator, cn } from "@identitycore/ui";

interface MarketingHeaderProps {
  activePath?: string;
  rightSlot?: ReactNode;
}

const NAV_LINKS = [
  { href: "/pricing", label: "Pricing" },
  { href: "/security", label: "Security" },
  { href: "/company", label: "Company" },
];

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

export function MarketingHeader({
  activePath,
  rightSlot,
}: MarketingHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center px-4 sm:px-6">
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
          className="ml-auto hidden items-center gap-1 md:flex"
        >
          {NAV_LINKS.map((link) => (
            <MarketingNavLink
              key={link.href}
              href={link.href}
              active={activePath === link.href}
            >
              {link.label}
            </MarketingNavLink>
          ))}

          <Separator orientation="vertical" className="mx-3 h-4" />

          <MarketingExternalLink href={DOCS_URL}>
            Documentation
          </MarketingExternalLink>

          {rightSlot ?? (
            <>
              <MarketingNavLink href="/login">Sign in</MarketingNavLink>

              <Button asChild size="sm" className="ml-2">
                <Link href="/register">Create workspace</Link>
              </Button>
            </>
          )}
        </nav>

        <button
          type="button"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="mobile-marketing-menu"
          onClick={() => setMenuOpen((open) => !open)}
          className="ml-auto inline-flex size-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
        >
          {menuOpen ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>

      {menuOpen && (
        <div
          id="mobile-marketing-menu"
          className="border-t border-border bg-background px-4 pb-4 pt-2 md:hidden"
        >
          <nav aria-label="Mobile navigation" className="flex flex-col">
            {NAV_LINKS.map((link) => (
              <MarketingNavLink
                key={link.href}
                href={link.href}
                active={activePath === link.href}
                mobile
                onClick={closeMenu}
              >
                {link.label}
              </MarketingNavLink>
            ))}

            <MarketingExternalLink href={DOCS_URL} mobile>
              Documentation
            </MarketingExternalLink>

            <Separator className="my-2" />

            {rightSlot ?? (
              <div className="grid grid-cols-2 gap-2 px-3 pt-1">
                <Link
                  href="/login"
                  onClick={closeMenu}
                  className="rounded-md border border-border px-3 py-2 text-center text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                >
                  Sign in
                </Link>

                <Button asChild size="sm">
                  <Link href="/register" onClick={closeMenu}>
                    Create workspace
                  </Link>
                </Button>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

interface MarketingNavLinkProps {
  href: string;
  active?: boolean;
  mobile?: boolean;
  children: ReactNode;
  onClick?: () => void;
}

function MarketingNavLink({
  href,
  active,
  mobile,
  children,
  onClick,
}: MarketingNavLinkProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      onClick={onClick}
      className={cn(
        "rounded-md text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        mobile ? "px-3 py-2.5" : "px-3 py-1.5",
        active
          ? "font-medium text-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
    </Link>
  );
}

interface MarketingExternalLinkProps {
  href: string;
  mobile?: boolean;
  children: ReactNode;
}

function MarketingExternalLink({
  href,
  mobile,
  children,
}: MarketingExternalLinkProps) {
  return (
    <a
      href={href}
      className={cn(
        "rounded-md text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        mobile ? "px-3 py-2.5" : "px-3 py-1.5",
      )}
    >
      {children}
    </a>
  );
}

function MenuIcon() {
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
