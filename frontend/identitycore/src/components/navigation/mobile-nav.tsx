"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Button, Separator } from "@identitycore/ui";
import type { NavGroup } from "./nav-data";

interface MobileNavProps {
  groups: NavGroup[];
  onNavigate: () => void;
  activePath?: string;
}

export function MobileNav({ groups, onNavigate, activePath }: MobileNavProps) {
  return (
    <div
      id="mobile-marketing-menu"
      className="border-t border-border bg-background px-4 pb-5 pt-3 md:hidden"
    >
      <nav aria-label="Mobile navigation" className="space-y-5">
        {groups.map((group) => (
          <div key={group.label}>
            <p className="px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {group.label}
            </p>

            <div className="mt-2 grid gap-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const content = (
                  <>
                    <Icon className="h-4 w-4 shrink-0 text-blue-600" />
                    <span className="min-w-0 flex-1">{item.label}</span>
                    {item.external ? (
                      <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                    ) : null}
                  </>
                );

                return item.external ? (
                  <a
                    key={item.label}
                    href={item.href}
                    onClick={onNavigate}
                    className={
                      item.href === activePath
                        ? "flex items-center gap-3 rounded-xl bg-blue-50 px-3 py-2.5 text-sm font-medium text-blue-700"
                        : "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    }
                  >
                    {content}
                  </a>
                ) : (
                  <Link
                    key={item.label}
                    href={item.href}
                    onClick={onNavigate}
                    className={
                      item.href === activePath
                        ? "flex items-center gap-3 rounded-xl bg-blue-50 px-3 py-2.5 text-sm font-medium text-blue-700"
                        : "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    }
                  >
                    {content}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}

        <Separator />

        <div className="grid grid-cols-2 gap-2 px-3">
          <Button asChild variant="outline" size="sm">
            <Link href="/login" onClick={onNavigate}>
              Sign in
            </Link>
          </Button>

          <Button asChild size="sm">
            <Link href="/register" onClick={onNavigate}>
              Create workspace
            </Link>
          </Button>
        </div>
      </nav>
    </div>
  );
}
