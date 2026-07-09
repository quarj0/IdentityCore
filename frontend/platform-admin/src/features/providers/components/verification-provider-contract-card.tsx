import { SectionCard } from "@/components/shared/section-card";
import type { VerificationProvider } from "@/features/providers/mock-data";
import { providerContractNotes } from "@/features/providers/mock-data";

type VerificationProviderContractCardProps = {
  provider: VerificationProvider;
};

export function VerificationProviderContractCard({
  provider,
}: VerificationProviderContractCardProps) {
  return (
    <SectionCard
      title="Contract and pricing"
      description="Commercial and compliance readiness for this provider."
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Pricing model</p>
          <p className="mt-2 font-semibold text-slate-950">{provider.pricingModel}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Estimated cost</p>
          <p className="mt-2 font-semibold text-slate-950">{provider.estimatedCost}</p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {providerContractNotes.map((note) => (
          <div key={note} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
            {note}
          </div>
        ))}
      </div>
    </SectionCard>
  );
}