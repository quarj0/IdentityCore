import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { VerificationProviderCapabilitiesCard } from "@/features/providers/components/verification-provider-capabilities-card";
import { VerificationProviderContractCard } from "@/features/providers/components/verification-provider-contract-card";
import { VerificationProviderCoverageCard } from "@/features/providers/components/verification-provider-coverage-card";
import { VerificationProviderHeader } from "@/features/providers/components/verification-provider-header";
import { VerificationProviderUsageCard } from "@/features/providers/components/verification-provider-usage-card";
import { getVerificationProviderById } from "@/features/providers/mock-data";

type VerificationProviderDetailPageProps = {
  providerId: string;
};

export function VerificationProviderDetailPage({
  providerId,
}: VerificationProviderDetailPageProps) {
  const provider = getVerificationProviderById(providerId);

  if (!provider) {
    return (
      <EmptyState
        title="Verification provider not found"
        description="This provider may have been removed or not configured in this environment."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/providers" className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500">
          Verification Providers
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{provider.name}</span>
      </nav>

      <VerificationProviderHeader provider={provider} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <VerificationProviderCapabilitiesCard provider={provider} />
          <VerificationProviderContractCard provider={provider} />
          <VerificationProviderUsageCard />
        </div>

        <div className="space-y-4">
          <VerificationProviderCoverageCard provider={provider} />
        </div>
      </div>
    </div>
  );
}