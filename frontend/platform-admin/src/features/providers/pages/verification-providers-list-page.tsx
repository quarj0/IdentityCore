"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { verificationProviders } from "@/features/providers/mock-data";
import { VerificationProvidersTable } from "@/features/providers/tables/verification-providers-table";

export function VerificationProvidersListPage() {
  const [query, setQuery] = useState("");

  const filteredProviders = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return verificationProviders;

    return verificationProviders.filter((provider) =>
      [
        provider.name,
        provider.status,
        provider.category,
        provider.countries.join(" "),
        provider.capabilities.join(" "),
        provider.integrationStage,
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
        eyebrow="Future integrations"
        title="Verification Providers"
        description="Manage third-party verification providers such as Jumio, Persona, Onfido, MetaMap, Smile Identity, VerifyMe and ID Analyzer."
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
              placeholder="Search verification providers..."
              className="pl-10"
              aria-label="Search verification providers"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Status</Button>
            <Button variant="outline">Country</Button>
            <Button variant="outline">Capability</Button>
            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredProviders.length > 0 ? (
        <VerificationProvidersTable providers={filteredProviders} />
      ) : (
        <EmptyState
          title="No verification providers found"
          description="No provider matches the current search or filters."
        />
      )}
    </div>
  );
}