import { SectionCard } from "@/components/shared/section-card";
import { workflowUsage } from "@/features/workflows/mock-data";

export function WorkflowUsageCard() {
  return (
    <SectionCard
      title="Usage"
      description="Organizations currently running this workflow."
    >
      <div className="space-y-3">
        {workflowUsage.map((usage) => (
          <div
            key={usage.organization}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">{usage.organization}</p>
              <p className="mt-1 text-xs text-slate-500">{usage.environment}</p>
            </div>

            <p className="text-sm font-semibold text-slate-950">
              {usage.runs} runs
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}