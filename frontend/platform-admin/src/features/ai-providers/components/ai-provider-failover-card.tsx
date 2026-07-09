import { SectionCard } from "@/components/shared/section-card";
import type { AiProvider } from "@/features/ai-providers/mock-data";
import { aiProviderRoutingRules } from "@/features/ai-providers/mock-data";

type AiProviderFailoverCardProps = {
  provider: AiProvider;
};

export function AiProviderFailoverCard({ provider }: AiProviderFailoverCardProps) {
  return (
    <SectionCard
      title="Failover and routing"
      description="Priority, fallback behavior and routing rules."
    >
      <div className="mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4">
        <p className="text-sm text-blue-800">
          This provider is priority <span className="font-semibold">#{provider.priority}</span>.
          Failover is <span className="font-semibold">{provider.failoverEnabled ? "enabled" : "disabled"}</span>.
        </p>
      </div>

      <div className="space-y-3">
        {aiProviderRoutingRules.map((rule) => (
          <div key={rule.condition} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-950">{rule.condition}</p>
            <p className="mt-1 text-sm text-slate-600">{rule.action}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}