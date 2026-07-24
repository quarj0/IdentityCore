import { Button } from "@identitycore/ui";
import { CloneWorkflowDialog } from "@/features/workflows/forms/clone-workflow-dialog";
import { WorkflowArchiveDialog } from "@/features/workflows/components/workflow-archive-dialog";
import { WorkflowPublishDialog } from "@/features/workflows/components/workflow-publish-dialog";
import { WorkflowStatusPill } from "@/features/workflows/components/workflow-status-pill";
import type { WorkflowRecord } from "@/features/workflows/live-data";

type WorkflowHeaderProps = {
  workflow: WorkflowRecord;
  onChanged?: () => void;
};

export function WorkflowHeader({ workflow, onChanged }: WorkflowHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {workflow.name}
            </h1>
            <WorkflowStatusPill status={workflow.status} />
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {workflow.description}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Project</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{workflow.projectName}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Version</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">
                {workflow.version.toString()}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Created by</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{workflow.createdByEmail}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Updated</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{workflow.updatedAt}</dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline">Edit draft</Button>
          <CloneWorkflowDialog workflowName={workflow.name} workflowId={workflow.id} onComplete={onChanged} />
          {workflow.status !== "published" ? (
            <WorkflowPublishDialog workflowName={workflow.name} workflowId={workflow.id} onComplete={onChanged} />
          ) : (
            <WorkflowArchiveDialog workflowName={workflow.name} workflowId={workflow.id} onComplete={onChanged} />
          )}
        </div>
      </div>
    </section>
  );
}
