"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { docsNav } from "@/data/docs-nav";
import { endpoints } from "@/data/endpoints";

const searchIndex = [
  ...docsNav.flatMap((group) =>
    group.items.map((item) => ({
      href: item.href,
      title: item.label,
      description: item.description,
      section: group.title,
      keywords: `${item.label} ${item.description}`.toLowerCase(),
    })),
  ),
  ...endpoints.map((endpoint) => ({
    href: `/api-reference/${endpoint.slug}`,
    title: endpoint.title,
    description: endpoint.path,
    section: `API reference · ${endpoint.category}`,
    keywords: `${endpoint.title} ${endpoint.description} ${endpoint.path} ${endpoint.category}`.toLowerCase(),
  })),
];

export function DocsSearch() {
  const [query, setQuery] = useState("");
  const trimmedQuery = query.trim().toLowerCase();
  const results = useMemo(() => {
    if (!trimmedQuery) {
      return [];
    }

    return searchIndex
      .filter((item) => item.keywords.includes(trimmedQuery))
      .slice(0, 6);
  }, [trimmedQuery]);

  return (
    <div className="relative" role="search" aria-label="Documentation search">
      <Search
        className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        aria-hidden="true"
      />
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search documentation..."
        aria-label="Search documentation"
        aria-describedby="docs-search-help"
        className="h-11 w-full rounded-2xl border border-slate-200 bg-white pl-10 pr-4 text-sm outline-none placeholder:text-slate-400 focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
      />

      <p id="docs-search-help" className="mt-2 text-xs text-slate-500">
        Search docs pages and API endpoints by title, path, or topic.
      </p>

      {trimmedQuery ? (
        <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {results.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {results.map((result) => (
                <Link
                  key={result.href}
                  href={result.href}
                  className="block px-4 py-3 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-600"
                >
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {result.section}
                  </p>
                  <p className="mt-1 text-sm font-medium text-slate-950">
                    {result.title}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    {result.description}
                  </p>
                </Link>
              ))}
            </div>
          ) : (
            <p className="px-4 py-3 text-sm text-slate-600">
              No matches found for “{query}”.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
