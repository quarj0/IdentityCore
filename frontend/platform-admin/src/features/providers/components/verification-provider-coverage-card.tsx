import { SectionCard } from "@/components/shared/section-card";
import type { VerificationProvider } from "@/features/providers/mock-data";

type VerificationProviderCoverageCardProps = {
  provider: VerificationProvider;
};

export function VerificationProviderCoverageCard({
  provider,
}: VerificationProviderCoverageCardProps) {
  return (
    <SectionCard
      title="Coverage"
      description="Countries and regions supported by this provider."
    >
      <div className="flex flex-wrap gap-2">
        {provider.countries.map((country) => (
          <span
            key={country}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200"
          >
            {country}
          </span>
        ))}
      </div>
    </SectionCard>
  );
}