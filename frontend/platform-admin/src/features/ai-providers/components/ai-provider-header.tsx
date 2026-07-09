import { Button } from "@identitycore/ui";
import type { AiProvider } from "@/features/ai-providers/mock-data";
import { AiProviderDisableDialog } from "@/features/ai-providers/components/ai-provider-disable-dialog";
import { AiProviderStatusPill } from "@/features/ai-providers/components/ai-provider-status-pill";
import { AiProviderTestDialog } from "@/features/ai-providers/components/ai-provider-test-dialog";

type AiProviderHeaderProps = {
  provider: AiProvider;
};

export function AiProviderHeader({ provider }: AiProviderHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {provider.name}
            </h1>
            <AiProviderStatusPill status={provider.status} />
          </div>

          <p className="mt-2 text-sm text-slate-600">
            {provider.model} · {provider.region} · Priority #{provider.priority}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Type</dt>
              <dd className="mt-1 text-sm font-medium capitalize text-slate-950">{provider.type}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Owner</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{provider.ownerTeam}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Failover</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">
                {provider.failoverEnabled ? "Enabled" : "Disabled"}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Health check</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{provider.lastHealthCheckAt}</dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline">Edit routing</Button>
          <AiProviderTestDialog providerName={provider.name} />
          <AiProviderDisableDialog providerName={provider.name} />
        </div>
      </div>
    </section>
  );
}