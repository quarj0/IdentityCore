"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { downloadCsv } from "@/lib/export-csv";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import {
  fetchWorkflowRecords,
  type WorkflowRecord,
} from "@/features/workflows/live-data";
import { CreateWorkflowDialog } from "@/features/workflows/forms/create-workflow-dialog";
import { WorkflowsTable } from "@/features/workflows/tables/workflows-table";

export function WorkflowsListPage() {
  const [query, setQuery] = useState("");
  const [workflows, setWorkflows] = useState<WorkflowRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => { setLoading(true); setError(null); try { setWorkflows(await fetchWorkflowRecords()); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load workflows."); } finally { setLoading(false); } };

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchWorkflowRecords();
        if (active) {
          setWorkflows(data);
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load workflows.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const filteredWorkflows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return workflows;

    return workflows.filter((workflow) =>
      [
        workflow.name,
        workflow.description,
        workflow.status,
        workflow.projectName,
        workflow.version.toString(),
        workflow.createdByEmail,
        workflow.updatedAt,
        workflow.steps
          .map((step) => (typeof step === "string" ? step : JSON.stringify(step)))
          .join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query, workflows]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Official workflow library"
        title="Global Workflows"
        description="Manage official IdentityCore workflow blueprints that combine templates, provider routing, policies, risk checks and manual review."
        actions={
          <>
            <Button variant="outline" onClick={() => downloadCsv("workflows.csv", workflows.map((workflow) => ({ id: workflow.id, name: workflow.name, status: workflow.status, description: workflow.description })))}>Export</Button>
            <CreateWorkflowDialog onCreated={reload} />
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

        </div>
      </section>

      {error ? (
        <EmptyState title="Unable to load workflows" description={error} />
      ) : loading && workflows.length === 0 ? (
        <PageHeader
          eyebrow="Official workflow library"
          title="Loading workflows"
          description="Fetching live workflow data from the backend."
        />
      ) : filteredWorkflows.length > 0 ? (
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
