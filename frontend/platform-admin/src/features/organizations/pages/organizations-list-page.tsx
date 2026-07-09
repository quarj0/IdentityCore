"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { OrganizationsTable } from "@/features/organizations/tables/organizations-table";
import { organizations } from "@/features/organizations/mock-data";

export function OrganizationsListPage() {
  const [query, setQuery] = useState("");

  const filteredOrganizations = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return organizations;
    }

    return organizations.filter((organization) => {
      return [
        organization.name,
        organization.country,
        organization.industry,
        organization.ownerEmail,
        organization.status,
        organization.plan,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [query]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform administration"
        title="Organizations"
        description="Manage every organization using IdentityCore, including onboarding status, subscriptions, usage, domains, branding, risk, suspension and lifecycle actions."
        actions={
          <>
            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Export
            </Button>
            <Button>Review onboarding</Button>
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
              placeholder="Search organizations..."
              className="border-slate-200 bg-white/5 pl-10 text-slate-100 placeholder:text-slate-500"
              aria-label="Search organizations"
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
              Plan
            </Button>

            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Risk
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

      {filteredOrganizations.length > 0 ? (
        <OrganizationsTable organizations={filteredOrganizations} />
      ) : (
        <EmptyState
          title="No organizations found"
          description="No organization matches the current search or filters. Clear your search and try again."
        />
      )}
    </div>
  );
}
