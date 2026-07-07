import Link from "next/link";
import { docsNav } from "@/data/docs-nav";

export function MobileDocsNav() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 lg:hidden">
      <p className="text-sm font-semibold">Developer sections</p>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {docsNav.flatMap((group) =>
          group.items.map((item) => {
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
              >
                <Icon className="h-4 w-4 text-blue-600" />
                {item.label}
              </Link>
            );
          }),
        )}
      </div>
    </div>
  );
}
