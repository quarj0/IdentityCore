import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import { aiProviderHealth } from "@/features/dashboard/mock-data";

export function AiProviderHealth() {
  return (
    <SectionCard
      title="AI provider health"
      description="Provider health, latency, success rate, cost and failover priority."
    >
      <div className="space-y-4">
        {aiProviderHealth.map((provider) => (
          <div
            key={provider.name}
            className="rounded-2xl border border-white/10 bg-slate-950/40 p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {provider.name}
                </h3>
                <p className="mt-1 text-sm text-slate-400">{provider.type}</p>
              </div>

              <StatusPill
                tone={provider.status === "Operational" ? "success" : "warning"}
              >
                {provider.status}
              </StatusPill>
            </div>

            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">Latency</dt>
                <dd className="mt-1 font-medium text-slate-200">
                  {provider.latency}
                </dd>
              </div>

              <div>
                <dt className="text-slate-500">Success</dt>
                <dd className="mt-1 font-medium text-slate-200">
                  {provider.successRate}
                </dd>
              </div>

              <div>
                <dt className="text-slate-500">Cost</dt>
                <dd className="mt-1 font-medium text-slate-200">
                  {provider.cost}
                </dd>
              </div>

              <div>
                <dt className="text-slate-500">Priority</dt>
                <dd className="mt-1 font-medium text-slate-200">
                  Failover #{provider.priority}
                </dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
