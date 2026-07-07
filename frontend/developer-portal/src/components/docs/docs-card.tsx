import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";

interface DocsCardProps {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

export function DocsCard({
  href,
  label,
  description,
  icon: Icon,
}: DocsCardProps) {
  return (
    <Link
      href={href}
      className="group rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>

      <h2 className="mt-6 font-semibold">{label}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>

      <div className="mt-6 flex items-center gap-2 text-sm font-medium text-blue-600">
        Read guide
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
