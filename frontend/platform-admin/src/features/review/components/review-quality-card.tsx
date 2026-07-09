import { SectionCard } from "@/components/shared/section-card";
import { qualityChecklist } from "@/features/review/mock-data";

export function ReviewQualityCard() {
  return (
    <SectionCard
      title="Quality control"
      description="Checklist reviewers must satisfy before final decision."
    >
      <div className="space-y-3">
        {qualityChecklist.map((item) => (
          <label
            key={item}
            className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700"
          >
            <input
              type="checkbox"
              className="mt-1 size-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span>{item}</span>
          </label>
        ))}
      </div>
    </SectionCard>
  );
}