"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LockKeyhole, Settings2, UserRound } from "lucide-react";

const items = [
  { href: "/settings", label: "Workspace", icon: Settings2 },
  { href: "/settings/profile", label: "Profile", icon: UserRound },
  { href: "/settings/security", label: "Security", icon: LockKeyhole },
];

export function SettingsNavigation() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Settings sections"
      className="flex w-fit max-w-full gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1 shadow-sm"
    >
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
              active
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
