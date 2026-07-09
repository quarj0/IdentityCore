import Link from "next/link";
import { ChevronRight } from "lucide-react";

interface Crumb {
  label: string;
  href?: string;
}

export function DashboardBreadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-500">
        {items.map((item, index) => (
          <li key={item.label} className="flex items-center gap-2">
            {item.href ? (
              <Link href={item.href} className="hover:text-slate-950">
                {item.label}
              </Link>
            ) : (
              <span className="font-medium text-slate-950">{item.label}</span>
            )}

            {index < items.length - 1 ? (
              <ChevronRight className="h-4 w-4" />
            ) : null}
          </li>
        ))}
      </ol>
    </nav>
  );
}
