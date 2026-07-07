"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldAlert } from "lucide-react";
import { Badge, BrandMark, ThemeToggle, cn } from "@identitycore/ui";
import { adminNav } from "@/lib/admin-data";

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="border-r border-border bg-card px-5 py-6">
          <div className="sticky top-6 space-y-8">
            <BrandMark subtitle="Platform admin" />
            <div className="rounded-lg border border-border bg-muted/40 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <ShieldAlert className="h-4 w-4 text-primary" />
                Internal use only
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Focus this console on approvals, operational health, and cross-tenant trust risk.
              </p>
            </div>
            <nav className="space-y-1">
              {adminNav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "block rounded-md px-3 py-2 text-sm transition-colors",
                    pathname === item.href || pathname.startsWith(`${item.href}/`)
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
              <Badge variant="destructive" className="hidden sm:inline-flex">Restricted</Badge>
              <ThemeToggle />
            </div>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-xl">
            <div className="flex h-16 items-center justify-between px-6 lg:px-8">
              <div>
                <div className="text-sm font-medium text-foreground">Platform trust operations</div>
                <div className="text-xs text-muted-foreground">Cross-tenant visibility for approvals, abuse, and service posture.</div>
              </div>
              <Badge variant="warning">4 active incidents</Badge>
            </div>
          </header>
          <main id="main-content" className="px-6 py-8 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
