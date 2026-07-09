import type { GlobalWorkflow } from "@/features/workflows/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type WorkflowStepsCardProps = {
  workflow: GlobalWorkflow;
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
            key={step}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-sm font-semibold text-slate-950">
              {index + 1}. {step}
            </p>
          </li>
        ))}
      </ol>
    </SectionCard>
  );
}