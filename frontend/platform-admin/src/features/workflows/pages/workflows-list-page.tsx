"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { CreateWorkflowDialog } from "@/features/workflows/forms/create-workflow-dialog";
import { globalWorkflows } from "@/features/workflows/mock-data";
import { WorkflowsTable } from "@/features/workflows/tables/workflows-table";

export function WorkflowsListPage() {
  const [query, setQuery] = useState("");

  const filteredWorkflows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return globalWorkflows;

    return globalWorkflows.filter((workflow) =>
      [
        workflow.name,
        workflow.description,
        workflow.status,
        workflow.category,
        workflow.version,
        workflow.ownerTeam,
        workflow.countries.join(" "),
        workflow.linkedTemplates.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Official workflow library"
        title="Global Workflows"
        description="Manage official IdentityCore workflow blueprints that combine templates, provider routing, policies, risk checks and manual review."
        actions={
          <>
            <Button variant="outline">Export</Button>
            <CreateWorkflowDialog />
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
              placeholder="Search workflows..."
              className="pl-10"
              aria-label="Search workflows"
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

      {filteredWorkflows.length > 0 ? (
        <WorkflowsTable workflows={filteredWorkflows} />
      ) : (
        <EmptyState
          title="No workflows found"
          description="No workflow matches the current search or filters."
        />
      )}
    </div>
  );
}