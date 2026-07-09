import { SectionCard } from "@/components/shared/section-card";
import { reviewerPerformance } from "@/features/review/mock-data";

export function ReviewerPerformanceCard() {
  return (
    <SectionCard
      title="Reviewer performance"
      description="Assignment load, completion rate and review accuracy."
    >
      <div className="space-y-3">
        {reviewerPerformance.map((reviewer) => (
          <div key={reviewer.reviewer} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-950">{reviewer.reviewer}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {reviewer.completed}/{reviewer.assigned} completed
                </p>
              </div>

              <p className="text-sm font-semibold text-slate-950">
                {reviewer.accuracy}
              </p>
            </div>

            <p className="mt-2 text-xs text-slate-500">
              Avg handle time: {reviewer.avgHandleTime}
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}