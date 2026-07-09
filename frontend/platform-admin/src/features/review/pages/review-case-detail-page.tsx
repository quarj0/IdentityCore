import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { ReviewCaseHeader } from "@/features/review/components/review-case-header";
import { ReviewEvidenceCard } from "@/features/review/components/review-evidence-card";
import { ReviewQualityCard } from "@/features/review/components/review-quality-card";
import { ReviewRecommendationCard } from "@/features/review/components/review-recommendation-card";
import { ReviewerPerformanceCard } from "@/features/review/components/reviewer-performance-card";
import { ReviewSummaryCards } from "@/features/review/components/review-summary-cards";
import { getReviewCaseById } from "@/features/review/mock-data";

type ReviewCaseDetailPageProps = {
  caseId: string;
};

export function ReviewCaseDetailPage({ caseId }: ReviewCaseDetailPageProps) {
  const reviewCase = getReviewCaseById(caseId);

  if (!reviewCase) {
    return (
      <EmptyState
        title="Review case not found"
        description="This case may have already been completed, archived or removed."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/review" className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500">
          Manual Review
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{reviewCase.id}</span>
      </nav>

      <ReviewCaseHeader reviewCase={reviewCase} />
      <ReviewSummaryCards reviewCase={reviewCase} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <ReviewEvidenceCard />
          <ReviewQualityCard />
        </div>

        <div className="space-y-4">
          <ReviewRecommendationCard reviewCase={reviewCase} />
          <ReviewerPerformanceCard />
        </div>
      </div>
    </div>
  );
}