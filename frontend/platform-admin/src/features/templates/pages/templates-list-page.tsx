"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { CreateTemplateDialog } from "@/features/templates/forms/create-template-dialog";
import { TemplatesTable } from "@/features/templates/tables/templates-table";
import { fetchTemplateRecords } from "@/features/templates/live-data";
import type { GlobalTemplate } from "@/features/templates/mock-data";

export function TemplatesListPage() {
  const [query, setQuery] = useState("");
  const [templates, setTemplates] = useState<GlobalTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTemplateRecords();
        if (active) {
          setTemplates(
            data.map((record) => ({
              id: record.id,
              name: record.title,
              description: record.subtitle,
              category: record.primaryMeta as GlobalTemplate["category"],
              status: record.status as GlobalTemplate["status"],
              version: record.secondaryMeta,
              countries: [],
              requiredChecks: [],
              usageCount: 0,
              clonedByOrganizations: 0,
              lastUpdatedAt: record.updatedAt,
              createdBy: "Backend",
              riskLevel: "Low" as GlobalTemplate["riskLevel"],
            })),
          );
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load templates.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const filteredTemplates = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return templates;

    return templates.filter((template) =>
      [
        template.name,
        template.description,
        template.category,
        template.status,
        template.version,
        template.riskLevel,
        template.countries.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query, templates]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Official library"
        title="Global Templates"
        description="Manage official IdentityCore templates used by organizations for verification, compliance and identity workflows."
        actions={
          <>
            <Button variant="outline">Export</Button>
            <CreateTemplateDialog />
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
              placeholder="Search templates..."
              className="pl-10"
              aria-label="Search templates"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Status</Button>
            <Button variant="outline">Category</Button>
            <Button variant="outline">Country</Button>
            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" aria-hidden="true" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {error ? (
        <EmptyState title="Unable to load templates" description={error} />
      ) : loading && templates.length === 0 ? (
        <PageHeader
          eyebrow="Official library"
          title="Loading templates"
          description="Fetching live templates from the backend."
        />
      ) : filteredTemplates.length > 0 ? (
        <TemplatesTable templates={filteredTemplates} />
      ) : (
        <EmptyState
          title="No templates found"
          description="No template matches the current search or filters."
        />
      )}
    </div>
  );
}
