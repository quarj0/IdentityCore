import { SectionCard } from "@/components/shared/section-card";
import type { AiProvider } from "@/features/ai-providers/mock-data";

type AiProviderCostCardProps = {
  provider: AiProvider;
};

export function AiProviderCostCard({ provider }: AiProviderCostCardProps) {
  return (
    <SectionCard
      title="Cost"
      description="Provider unit cost and monthly spend."
    >
      <div className="space-y-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Cost per check</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{provider.costPerCheck}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Monthly cost</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">{provider.monthlyCost}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Checks this month</p>
          <p className="mt-2 text-xl font-semibold text-slate-950">
            {provider.checksThisMonth.toLocaleString()}
          </p>
        </div>
      </div>
    </SectionCard>
  );
}