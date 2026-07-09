import { Activity, Clock3, CreditCard, Gauge } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import type { AiProvider } from "@/features/ai-providers/mock-data";

type AiProviderSummaryCardsProps = {
  provider: AiProvider;
};

export function AiProviderSummaryCards({ provider }: AiProviderSummaryCardsProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Checks today"
        value={provider.checksToday.toLocaleString()}
        change="+9.2%"
        trend={provider.checksToday > 0 ? "up" : "neutral"}
        helperText="24 hours"
        icon={Activity}
      />

      <MetricCard
        label="Latency"
        value={provider.latencyMs > 0 ? `${provider.latencyMs}ms` : "Paused"}
        change={`p95 ${provider.p95LatencyMs}ms`}
        trend={provider.latencyMs > 0 && provider.latencyMs < 300 ? "up" : "down"}
        helperText="average"
        icon={Clock3}
      />

      <MetricCard
        label="Success rate"
        value={provider.successRate}
        change={provider.errorRate}
        trend={provider.status === "operational" ? "up" : "down"}
        helperText="error rate"
        icon={Gauge}
      />

      <MetricCard
        label="Monthly cost"
        value={provider.monthlyCost}
        change={provider.costPerCheck}
        trend="neutral"
        helperText="per check"
        icon={CreditCard}
      />
    </section>
  );
}