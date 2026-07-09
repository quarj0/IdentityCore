import { AlertTriangle, BrainCircuit, Clock3, ShieldCheck } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import type { ReviewCase } from "@/features/review/mock-data";

type ReviewSummaryCardsProps = {
  reviewCase: ReviewCase;
};

export function ReviewSummaryCards({ reviewCase }: ReviewSummaryCardsProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Risk score"
        value={reviewCase.riskScore.toString()}
        change={reviewCase.priority}
        trend={reviewCase.riskScore > 70 ? "down" : "neutral"}
        helperText="risk"
        icon={AlertTriangle}
      />

      <MetricCard
        label="AI recommendation"
        value={reviewCase.aiRecommendation}
        change="Model output"
        trend="neutral"
        helperText="AI"
        icon={BrainCircuit}
      />

      <MetricCard
        label="SLA due"
        value={reviewCase.slaDueAt}
        change="Queue SLA"
        trend="neutral"
        helperText="review"
        icon={Clock3}
      />

      <MetricCard
        label="Checks"
        value={reviewCase.checks.length.toString()}
        change="Completed"
        trend="up"
        helperText="evidence"
        icon={ShieldCheck}
      />
    </section>
  );
}