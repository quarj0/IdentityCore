import { SectionCard } from "@/components/shared/section-card";
import { workflowVersions } from "@/features/workflows/mock-data";

export function WorkflowVersionHistoryCard() {
  return (
    <SectionCard
      title="Version history"
      description="Workflow version releases and change history."
    >
      <div className="space-y-3">
        {workflowVersions.map((version) => (
          <div
            key={version.version}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-950">{version.version}</p>
                <p className="mt-1 text-sm text-slate-600">{version.notes}</p>
              </div>

              <div className="flex items-center gap-2">
                <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200">
                  {version.status}
                </span>
                <span className="text-xs text-slate-500">{version.date}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}