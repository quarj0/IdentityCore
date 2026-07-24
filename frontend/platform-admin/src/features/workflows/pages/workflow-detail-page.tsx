"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { WorkflowBuilderPreview } from "@/features/workflows/components/workflow-builder-preview";
import { WorkflowHeader } from "@/features/workflows/components/workflow-header";
import { WorkflowStepsCard } from "@/features/workflows/components/workflow-steps-card";
import { WorkflowTemplateLinksCard } from "@/features/workflows/components/workflow-template-links-card";
import { WorkflowUsageCard } from "@/features/workflows/components/workflow-usage-card";
import { WorkflowVersionHistoryCard } from "@/features/workflows/components/workflow-version-history-card";
import {
  fetchWorkflowRecord,
  type WorkflowRecord,
  type WorkflowVersionRecord,
} from "@/features/workflows/live-data";

type WorkflowDetailPageProps = {
  workflowId: string;
};

export function WorkflowDetailPage({ workflowId }: WorkflowDetailPageProps) {
  const [workflow, setWorkflow] = useState<WorkflowRecord | null>(null);
  const [versions, setVersions] = useState<WorkflowVersionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchWorkflowRecord(workflowId);
        if (!active) return;
        setWorkflow(data.workflow);
        setVersions(data.versions);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load this workflow.",
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
  }, [workflowId, reloadKey]);

  if (loading && !workflow) {
    return (
      <EmptyState
        title="Loading workflow"
        description="Fetching live workflow data from the backend."
      />
    );
  }

  if (error && !workflow) {
    return (
      <EmptyState
        title="Workflow not found"
        description={error}
      />
    );
  }

  if (!workflow) {
    return (
      <EmptyState
        title="Workflow not found"
        description="This workflow may have been archived, deleted or moved to another environment."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link
          href="/workflows"
          className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          Workflows
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{workflow.name}</span>
      </nav>

      <WorkflowHeader workflow={workflow} onChanged={() => setReloadKey((key) => key + 1)} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <WorkflowBuilderPreview workflow={workflow} />
          <WorkflowStepsCard workflow={workflow} />
          <WorkflowVersionHistoryCard versions={versions} />
          <WorkflowUsageCard workflow={workflow} />
        </div>

        <div className="space-y-4">
          <WorkflowTemplateLinksCard workflow={workflow} />
        </div>
      </div>
    </div>
  );
}
