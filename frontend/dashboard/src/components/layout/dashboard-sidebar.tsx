"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandMark, cn } from "@identitycore/ui";
import { dashboardNav } from "@/data/dashboard-nav";

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden border-r border-slate-200 bg-white lg:block">
      <div className="sticky top-0 flex h-screen w-72 flex-col">
        <div className="border-b border-slate-200 px-6 py-5">
          <Link href="/" aria-label="IdentityCore dashboard home">
            <BrandMark subtitle="Workspace dashboard" />
          </Link>
        </div>

        <nav className="flex-1 space-y-7 overflow-y-auto px-4 py-6">
          {dashboardNav.map((group) => (
            <div key={group.title}>
              <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {group.title}
              </p>

              <div className="mt-2 grid gap-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
                        active
                          ? "bg-blue-50 text-blue-700"
                          : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
                      )}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
}
