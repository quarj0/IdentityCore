"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { tenants } from "@/features/tenants/mock-data";
import { TenantsTable } from "@/features/tenants/tables/tenants-table";

export function TenantsListPage() {
  const [query, setQuery] = useState("");

  const filteredTenants = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return tenants;
    }

    return tenants.filter((tenant) => {
      return [
        tenant.name,
        tenant.slug,
        tenant.organizationName,
        tenant.status,
        tenant.region,
        tenant.isolationModel,
        tenant.databaseName,
        tenant.environment,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [query]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform infrastructure"
        title="Tenants"
        description="Monitor and manage tenant environments, regions, isolation boundaries, storage, database health and operational status across IdentityCore."
        actions={
          <>
            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Export
            </Button>
            <Button>Provision tenant</Button>
          </>
        }
      />

      <section className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500"
              aria-hidden="true"
            />

            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search tenants..."
              className="border-slate-200 bg-white/5 pl-10 text-slate-100 placeholder:text-slate-500"
              aria-label="Search tenants"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Status
            </Button>

            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Region
            </Button>

            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Isolation
            </Button>

            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              <SlidersHorizontal className="mr-2 size-4" aria-hidden="true" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredTenants.length > 0 ? (
        <TenantsTable tenants={filteredTenants} />
      ) : (
        <EmptyState
          title="No tenants found"
          description="No tenant matches the current search or filters. Clear your search and try again."
        />
      )}
    </div>
  );
}
