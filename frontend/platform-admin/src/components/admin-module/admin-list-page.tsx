"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { AdminRecordTable } from "@/components/admin-module/admin-record-table";
import type { AdminModuleConfig } from "@/components/admin-module/admin-module-types";

type AdminListPageProps = {
  config: AdminModuleConfig;
};

export function AdminListPage({ config }: AdminListPageProps) {
  const [query, setQuery] = useState("");

  const filteredRecords = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return config.records;
    }

    return config.records.filter((record) =>
      [
        record.title,
        record.subtitle,
        record.status,
        record.primaryMeta,
        record.secondaryMeta,
        record.tertiaryMeta,
        record.owner,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [config.records, query]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow={config.moduleLabel}
        title={config.listTitle}
        description={config.listDescription}
        actions={
          <>
            <Button variant="outline">{config.exportLabel}</Button>
            <Button>{config.createLabel}</Button>
          </>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={config.searchPlaceholder}
              className="pl-10"
              aria-label={config.searchPlaceholder}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {config.filters.map((filter) => (
              <Button key={filter} variant="outline">
                {filter}
              </Button>
            ))}

            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" aria-hidden="true" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredRecords.length > 0 ? (
        <AdminRecordTable records={filteredRecords} />
      ) : (
        <EmptyState
          title={`No ${config.listTitle.toLowerCase()} found`}
          description="No record matches the current search or filters."
        />
      )}
    </div>
  );
}