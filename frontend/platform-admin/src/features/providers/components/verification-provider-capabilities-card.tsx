import { SectionCard } from "@/components/shared/section-card";
import type { VerificationProvider } from "@/features/providers/mock-data";

type VerificationProviderCapabilitiesCardProps = {
  provider: VerificationProvider;
};

export function VerificationProviderCapabilitiesCard({
  provider,
}: VerificationProviderCapabilitiesCardProps) {
  return (
    <SectionCard
      title="Capabilities"
      description="Verification capabilities this provider can support."
    >
      <div className="flex flex-wrap gap-2">
        {provider.capabilities.map((capability) => (
          <span
            key={capability}
            className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 ring-1 ring-blue-100"
          >
            {capability}
          </span>
        ))}
      </div>
    </SectionCard>
  );
}