import { SectionCard } from "@/components/shared/section-card";
import type { WorkflowRecord } from "@/features/workflows/live-data";
import { normalizeWorkflowUsage } from "@/features/workflows/live-data";

type WorkflowUsageCardProps = {
  workflow: WorkflowRecord;
};

export function WorkflowUsageCard({ workflow }: WorkflowUsageCardProps) {
  const usage = normalizeWorkflowUsage(workflow);
  return (
    <SectionCard
      title="Usage"
      description="Organizations currently running this workflow."
    >
      <div className="space-y-3">
        {usage.length > 0 ? usage.map((item) => (
          <div
            key={item.organization}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">{item.organization}</p>
              <p className="mt-1 text-xs text-slate-500">{item.environment}</p>
            </div>

            <p className="text-sm font-semibold text-slate-950">
              {item.runs} runs
            </p>
          </div>
        )) : (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-950">No usage telemetry available</p>
            <p className="mt-1 text-xs text-slate-500">
              The workflow record does not include organization usage metrics yet.
            </p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}
