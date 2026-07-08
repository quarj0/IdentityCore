"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { docsNav } from "@/data/docs-nav";
import { isDocsPathActive } from "@/lib/docs-navigation";

export function MobileDocsNav() {
  const pathname = usePathname();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 lg:hidden">
      <p className="text-sm font-semibold">Developer sections</p>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {docsNav.flatMap((group) =>
          group.items.map((item) => {
            const Icon = item.icon;
            const active = isDocsPathActive(pathname, item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={
                  active
                    ? "flex items-center gap-2 rounded-xl bg-blue-50 px-3 py-2 text-sm text-blue-700 ring-1 ring-blue-100"
                    : "flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                }
              >
                <Icon
                  className={active ? "h-4 w-4 text-blue-700" : "h-4 w-4 text-blue-600"}
                />
                <span
                  className={active ? "font-semibold text-blue-700" : undefined}
                >
                  {item.label}
                </span>
              </Link>
            );
          }),
        )}
      </div>
    </div>
  );
}
