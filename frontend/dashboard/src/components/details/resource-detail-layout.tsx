import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Badge } from "@identitycore/ui";

interface ResourceDetailLayoutProps {
  backHref: string;
  backLabel: string;
  title: string;
  description: string;
  status?: string;
  children: ReactNode;
}

export function ResourceDetailLayout({
  backHref,
  backLabel,
  title,
  description,
  status = "Sandbox",
  children,
}: ResourceDetailLayoutProps) {
  return (
    <div className="space-y-8">
      <Link
        href={backHref}
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-950"
      >
        <ArrowLeft className="h-4 w-4" />
        {backLabel}
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Badge variant="secondary" className="rounded-full">
            {status}
          </Badge>

          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            {title}
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
            {description}
          </p>
        </div>
      </div>

      {children}
    </div>
  );
}
