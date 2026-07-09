import type { GlobalTemplate } from "@/features/templates/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type TemplateCategoriesCardProps = {
  template: GlobalTemplate;
};

export function TemplateCategoriesCard({ template }: TemplateCategoriesCardProps) {
  return (
    <SectionCard
      title="Coverage"
      description="Countries and required checks supported by this template."
    >
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-slate-950">Countries</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {template.countries.map((country) => (
              <span
                key={country}
                className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 ring-1 ring-blue-100"
              >
                {country}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-950">Required checks</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {template.requiredChecks.map((check) => (
              <span
                key={check}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200"
              >
                {check}
              </span>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}