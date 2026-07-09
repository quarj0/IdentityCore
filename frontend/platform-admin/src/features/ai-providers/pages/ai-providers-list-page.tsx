"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { aiProviders } from "@/features/ai-providers/mock-data";
import { AiProvidersTable } from "@/features/ai-providers/tables/ai-providers-table";

export function AiProvidersListPage() {
  const [query, setQuery] = useState("");

  const filteredProviders = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return aiProviders;

    return aiProviders.filter((provider) =>
      [
        provider.name,
        provider.type,
        provider.status,
        provider.model,
        provider.region,
        provider.ownerTeam,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="AI infrastructure"
        title="AI Providers"
        description="Manage face, OCR and liveness providers across health, latency, success rate, cost, failover and routing priority."
        actions={
          <>
            <Button variant="outline">Export</Button>
            <Button>Add provider</Button>
          </>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search AI providers..."
              className="pl-10"
              aria-label="Search AI providers"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Type</Button>
            <Button variant="outline">Status</Button>
            <Button variant="outline">Region</Button>
            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredProviders.length > 0 ? (
        <AiProvidersTable providers={filteredProviders} />
      ) : (
        <EmptyState
          title="No AI providers found"
          description="No AI provider matches the current search or filters."
        />
      )}
    </div>
  );
}