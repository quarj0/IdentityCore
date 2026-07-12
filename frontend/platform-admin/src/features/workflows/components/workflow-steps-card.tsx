import { SectionCard } from "@/components/shared/section-card";
import type { WorkflowRecord } from "@/features/workflows/live-data";

type WorkflowStepsCardProps = {
  workflow: WorkflowRecord;
};

export function WorkflowStepsCard({ workflow }: WorkflowStepsCardProps) {
  return (
    <SectionCard
      title="Workflow steps"
      description="Ordered verification, risk, review and delivery actions."
    >
      <ol className="space-y-3">
        {workflow.steps.map((step, index) => (
          <li
            key={`${index}-${JSON.stringify(step)}`}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-sm font-semibold text-slate-950">
              {index + 1}. {typeof step === "string" ? step : JSON.stringify(step)}
            </p>
          </li>
        ))}
      </ol>
    </SectionCard>
  );
}
