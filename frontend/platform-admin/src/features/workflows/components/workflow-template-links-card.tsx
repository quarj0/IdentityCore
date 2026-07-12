import { SectionCard } from "@/components/shared/section-card";
import type { WorkflowRecord } from "@/features/workflows/live-data";
import { normalizeLinkedTemplates } from "@/features/workflows/live-data";

type WorkflowTemplateLinksCardProps = {
  workflow: WorkflowRecord;
};

export function WorkflowTemplateLinksCard({ workflow }: WorkflowTemplateLinksCardProps) {
  const linkedTemplates = normalizeLinkedTemplates(workflow.settings);
  return (
    <SectionCard
      title="Linked templates"
      description="Official templates connected to this workflow."
    >
      <div className="space-y-3">
        {linkedTemplates.length > 0 ? linkedTemplates.map((template) => (
          <div
            key={template}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-sm font-medium text-slate-950">{template}</p>
            <p className="mt-1 text-xs text-slate-500">
              Used as a verification block in this workflow.
            </p>
          </div>
        )) : (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-950">No linked templates</p>
            <p className="mt-1 text-xs text-slate-500">
              The backend has not exposed template links for this workflow yet.
            </p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}
