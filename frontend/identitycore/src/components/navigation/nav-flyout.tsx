"use client";

import Link from "next/link";
import { ChevronDown, ExternalLink } from "lucide-react";
import { cn } from "@identitycore/ui";
import type { NavGroup } from "./nav-data";

interface NavFlyoutProps {
  group: NavGroup;
  activePath?: string;
}

export function NavFlyout({ group, activePath }: NavFlyoutProps) {
  const isActive = group.items.some((item) => item.href === activePath);

  return (
    <div className="group relative">
      <button
        type="button"
        className={cn(
          "inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          isActive
            ? "bg-blue-50 text-blue-700"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-haspopup="true"
      >
        {group.label}
        <ChevronDown className="h-3.5 w-3.5 transition-transform group-hover:rotate-180" />
      </button>

      <div className="invisible absolute left-1/2 top-full z-50 mt-3 w-[560px] -translate-x-1/2 opacity-0 transition-all duration-150 group-hover:visible group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100">
        <div className="rounded-3xl border border-slate-200 bg-white p-3 shadow-[0_24px_80px_rgba(15,23,42,0.14)]">
          <div className="grid gap-2 sm:grid-cols-2">
            {group.items.map((item) => {
              const Icon = item.icon;
              const className = cn(
                "group/item flex gap-4 rounded-2xl p-4 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              );

              const content = (
                <>
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="text-sm font-semibold text-foreground">
                        {item.label}
                      </p>
                      {item.external ? (
                        <ExternalLink
                          className="h-3.5 w-3.5 text-muted-foreground"
                          aria-hidden="true"
                        />
                      ) : null}
                    </div>

                    <p className="mt-1 text-sm leading-6 text-muted-foreground">
                      {item.description}
                    </p>
                  </div>
                </>
              );

              return item.external ? (
                <a key={item.label} href={item.href} className={className}>
                  {content}
                </a>
              ) : (
                <Link key={item.label} href={item.href} className={className}>
                  {content}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
