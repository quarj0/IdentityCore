"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { getDocsNavItems, getPrimaryDocsItem } from "@/lib/docs-navigation";
import { siteConfig } from "@/lib/site-config";

export function DocsFooter() {
  const pathname = usePathname();
  const items = getDocsNavItems();
  const currentItem = getPrimaryDocsItem(pathname);
  const currentIndex = currentItem
    ? items.findIndex((item) => item.href === currentItem.href)
    : -1;
  const previousItem = currentIndex > 0 ? items[currentIndex - 1] : undefined;
  const nextItem =
    currentIndex >= 0 && currentIndex < items.length - 1
      ? items[currentIndex + 1]
      : undefined;

  return (
    <footer className="mt-12 border-t border-slate-200 pt-8">
      <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div className="grid gap-4 sm:grid-cols-2">
          {previousItem ? (
            <Link
              href={previousItem.href}
              className="rounded-2xl border border-slate-200 bg-white p-4 hover:border-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <ArrowLeft className="h-3.5 w-3.5" />
                Previous
              </p>
              <p className="mt-3 font-semibold text-slate-950">
                {previousItem.label}
              </p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                {previousItem.description}
              </p>
            </Link>
          ) : (
            <div className="hidden sm:block" />
          )}

          {nextItem ? (
            <Link
              href={nextItem.href}
              className="rounded-2xl border border-slate-200 bg-white p-4 hover:border-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              <p className="flex items-center justify-end gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Next
                <ArrowRight className="h-3.5 w-3.5" />
              </p>
              <p className="mt-3 text-right font-semibold text-slate-950">
                {nextItem.label}
              </p>
              <p className="mt-1 text-right text-sm leading-6 text-slate-600">
                {nextItem.description}
              </p>
            </Link>
          ) : null}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <p className="text-sm font-semibold text-slate-950">Need more context?</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Start in the getting started guide, test in sandbox, and create a
            workspace when you are ready to move from docs to implementation.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm font-medium">
            <Link href="/quickstart" className="text-blue-600 hover:text-blue-700">
              Open getting started guide
            </Link>
            <a
              href={siteConfig.createWorkspaceUrl}
              className="text-slate-700 hover:text-slate-950"
            >
              Create workspace
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
