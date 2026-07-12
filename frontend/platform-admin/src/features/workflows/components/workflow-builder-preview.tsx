import { GitBranch } from "lucide-react";
import { SectionCard } from "@/components/shared/section-card";
import type { WorkflowRecord } from "@/features/workflows/live-data";

type WorkflowBuilderPreviewProps = {
  workflow: WorkflowRecord;
};

export function WorkflowBuilderPreview({ workflow }: WorkflowBuilderPreviewProps) {
  return (
    <SectionCard
      title="Builder preview"
      description="Visual preview of this official workflow blueprint."
    >
      <div className="space-y-3">
        {workflow.steps.map((step, index) => (
          <div
            key={`${index}-${JSON.stringify(step)}`}
            className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex size-9 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
              <GitBranch className="size-4" aria-hidden="true" />
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-950">
                Step {index + 1}: {typeof step === "string" ? step : JSON.stringify(step)}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                This step is included when an organization uses or clones the workflow.
              </p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
