import { SectionCard } from "@/components/shared/section-card";
import { reviewEvidence } from "@/features/review/mock-data";

export function ReviewEvidenceCard() {
  return (
    <SectionCard
      title="Evidence"
      description="AI evidence and verification signals for this review case."
    >
      <div className="space-y-3">
        {reviewEvidence.map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-950">{item.label}</p>
            <p className="mt-1 text-sm text-slate-600">{item.value}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}