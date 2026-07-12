import { SectionCard } from "@/components/shared/section-card";
import type { TemplateRecord } from "@/features/templates/live-data";

type TemplateUsageCardProps = {
  template: TemplateRecord;
};

export function TemplateUsageCard({ template }: TemplateUsageCardProps) {
  const usage = [
    {
      label: "Usage count",
      value: template.usageCount.toLocaleString(),
      helper: "total executions",
    },
    {
      label: "Organizations cloned",
      value: template.clonedByOrganizations.toLocaleString(),
      helper: "workflow reuse",
    },
    {
      label: "Owner team",
      value: template.ownerTeam || "Platform",
      helper: "primary steward",
    },
    {
      label: "Risk level",
      value: template.riskLevel || "Not set",
      helper: "backend classification",
    },
  ];
  return (
    <SectionCard
      title="Usage"
      description="Live usage and adoption metrics from the backend."
    >
      <div className="space-y-3">
        {usage.map((item) => (
          <div
            key={item.label}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">{item.label}</p>
              <p className="mt-1 text-xs text-slate-500">{item.helper}</p>
            </div>

            <p className="text-sm font-semibold text-slate-950">{item.value}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
