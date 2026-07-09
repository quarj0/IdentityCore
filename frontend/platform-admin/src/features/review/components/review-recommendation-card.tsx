import { SectionCard } from "@/components/shared/section-card";
import type { ReviewCase } from "@/features/review/mock-data";

type ReviewRecommendationCardProps = {
  reviewCase: ReviewCase;
};

export function ReviewRecommendationCard({
  reviewCase,
}: ReviewRecommendationCardProps) {
  return (
    <SectionCard
      title="Recommendation"
      description="AI recommendation and policy reason."
    >
      <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
        <p className="text-sm text-amber-800">AI recommendation</p>
        <p className="mt-2 text-xl font-semibold text-amber-950">
          {reviewCase.aiRecommendation}
        </p>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-500">Reason</p>
        <p className="mt-2 text-sm font-medium leading-6 text-slate-950">
          {reviewCase.failureReason}
        </p>
      </div>
    </SectionCard>
  );
}