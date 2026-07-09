import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AiProviderCostCard } from "@/features/ai-providers/components/ai-provider-cost-card";
import { AiProviderFailoverCard } from "@/features/ai-providers/components/ai-provider-failover-card";
import { AiProviderHeader } from "@/features/ai-providers/components/ai-provider-header";
import { AiProviderHealthCard } from "@/features/ai-providers/components/ai-provider-health-card";
import { AiProviderLatencyCard } from "@/features/ai-providers/components/ai-provider-latency-card";
import { AiProviderSummaryCards } from "@/features/ai-providers/components/ai-provider-summary-cards";
import { getAiProviderById } from "@/features/ai-providers/mock-data";

type AiProviderDetailPageProps = {
  providerId: string;
};

export function AiProviderDetailPage({ providerId }: AiProviderDetailPageProps) {
  const provider = getAiProviderById(providerId);

  if (!provider) {
    return (
      <EmptyState
        title="AI provider not found"
        description="This provider may have been removed, disabled or moved to another environment."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/ai-providers" className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500">
          AI Providers
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{provider.name}</span>
      </nav>

      <AiProviderHeader provider={provider} />
      <AiProviderSummaryCards provider={provider} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <AiProviderLatencyCard provider={provider} />
          <AiProviderFailoverCard provider={provider} />
          <AiProviderHealthCard />
        </div>

        <div className="space-y-4">
          <AiProviderCostCard provider={provider} />
        </div>
      </div>
    </div>
  );
}