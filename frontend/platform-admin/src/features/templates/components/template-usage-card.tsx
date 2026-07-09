import { SectionCard } from "@/components/shared/section-card";
import { templateUsageByOrganization } from "@/features/templates/mock-data";

export function TemplateUsageCard() {
  return (
    <SectionCard
      title="Usage"
      description="Organizations currently using or testing this template."
    >
      <div className="space-y-3">
        {templateUsageByOrganization.map((usage) => (
          <div
            key={usage.organization}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">{usage.organization}</p>
              <p className="mt-1 text-xs text-slate-500">{usage.environment}</p>
            </div>

            <p className="text-sm font-semibold text-slate-950">
              {usage.monthlyVolume} / month
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}