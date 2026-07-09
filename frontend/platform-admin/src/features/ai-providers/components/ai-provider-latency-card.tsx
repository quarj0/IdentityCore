import { SectionCard } from "@/components/shared/section-card";
import type { AiProvider } from "@/features/ai-providers/mock-data";

type AiProviderLatencyCardProps = {
  provider: AiProvider;
};

export function AiProviderLatencyCard({ provider }: AiProviderLatencyCardProps) {
  const latencyItems = [
    { label: "Average latency", value: provider.latencyMs > 0 ? `${provider.latencyMs}ms` : "Paused" },
    { label: "p95 latency", value: provider.p95LatencyMs > 0 ? `${provider.p95LatencyMs}ms` : "Paused" },
    { label: "Success rate", value: provider.successRate },
    { label: "Error rate", value: provider.errorRate },
  ];

  return (
    <SectionCard
      title="Performance"
      description="Latency, reliability and request success metrics."
    >
      <dl className="grid gap-3 sm:grid-cols-2">
        {latencyItems.map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <dt className="text-sm text-slate-500">{item.label}</dt>
            <dd className="mt-2 text-lg font-semibold text-slate-950">{item.value}</dd>
          </div>
        ))}
      </dl>
    </SectionCard>
  );
}