import type { GlobalWorkflow } from "@/features/workflows/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type WorkflowTemplateLinksCardProps = {
  workflow: GlobalWorkflow;
};

export function WorkflowTemplateLinksCard({ workflow }: WorkflowTemplateLinksCardProps) {
  return (
    <SectionCard
      title="Linked templates"
      description="Official templates connected to this workflow."
    >
      <div className="space-y-3">
        {workflow.linkedTemplates.map((template) => (
          <div
            key={template}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-sm font-medium text-slate-950">{template}</p>
            <p className="mt-1 text-xs text-slate-500">
              Used as a verification block in this workflow.
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}