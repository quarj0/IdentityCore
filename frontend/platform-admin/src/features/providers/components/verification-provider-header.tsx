import { Button } from "@identitycore/ui";
import type { VerificationProvider } from "@/features/providers/mock-data";
import { VerificationProviderEnableDialog } from "@/features/providers/components/verification-provider-enable-dialog";
import { VerificationProviderStatusPill } from "@/features/providers/components/verification-provider-status-pill";

type VerificationProviderHeaderProps = {
  provider: VerificationProvider;
};

export function VerificationProviderHeader({
  provider,
}: VerificationProviderHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {provider.name}
            </h1>
            <VerificationProviderStatusPill status={provider.status} />
          </div>

          <p className="mt-2 text-sm text-slate-600">
            {provider.category} · {provider.integrationStage} · {provider.ownerTeam}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">API readiness</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{provider.apiReadiness}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Pricing</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{provider.pricingModel}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Latency</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">
                {provider.latencyMs > 0 ? `${provider.latencyMs}ms` : "N/A"}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Reviewed</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{provider.lastReviewedAt}</dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline">Edit notes</Button>
          <VerificationProviderEnableDialog providerName={provider.name} />
        </div>
      </div>
    </section>
  );
}