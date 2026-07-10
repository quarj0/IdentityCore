"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { cn } from "@identitycore/ui";
import { platformNavItems } from "@/components/navigation/platform-nav-items";

export function PlatformSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-200 bg-white/95 px-4 py-5 backdrop-blur lg:block">
      <Link href="/" className="flex items-center gap-3 px-2">
        <div className="flex size-10 items-center justify-center rounded-2xl bg-cyan-400/10 text-orange-500 ring-1 ring-orange-300/30">
          <ShieldCheck className="size-5" aria-hidden="true" />
        </div>

        <div>
          <p className="text-sm font-semibold text-slate-950">IdentityCore</p>
          <p className="text-xs text-slate-400">Platform Admin</p>
        </div>
      </Link>

      <nav className="mt-8 space-y-1" aria-label="Platform admin navigation">
        {platformNavItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium outline-none transition",
                "focus-visible:ring-2 focus-visible:ring-cyan-300",
                isActive
                  ? "bg-white text-slate-950"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-950",
              )}
            >
              <item.icon className="size-4" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
