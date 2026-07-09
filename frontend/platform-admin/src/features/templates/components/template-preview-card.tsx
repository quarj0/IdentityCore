import { FileCheck2 } from "lucide-react";
import type { GlobalTemplate } from "@/features/templates/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type TemplatePreviewCardProps = {
  template: GlobalTemplate;
};

export function TemplatePreviewCard({ template }: TemplatePreviewCardProps) {
  return (
    <SectionCard
      title="Template preview"
      description="High-level verification steps organizations will inherit."
    >
      <div className="space-y-3">
        {template.requiredChecks.map((check, index) => (
          <div
            key={check}
            className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex size-9 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
              <FileCheck2 className="size-4" aria-hidden="true" />
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-950">
                Step {index + 1}: {check}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                This check is enforced when organizations use this official template.
              </p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}