import { SectionCard } from "@/components/shared/section-card";
import type { TemplateRecord } from "@/features/templates/live-data";

type TemplateVersionCardProps = {
  template: TemplateRecord;
};

export function TemplateVersionCard({ template }: TemplateVersionCardProps) {
  return (
    <SectionCard
      title="Lifecycle"
      description="Live version and lifecycle data from the backend."
    >
      <div className="space-y-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-950">Current version</p>
              <p className="mt-1 text-sm text-slate-600">{template.version}</p>
            </div>

            <div className="flex items-center gap-2">
              <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200">
                {template.status}
              </span>
              <span className="text-xs text-slate-500">{template.updatedAt}</span>
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-950">Created</p>
          <p className="mt-1 text-sm text-slate-600">{template.createdAt}</p>
        </div>
      </div>
    </SectionCard>
  );
}
