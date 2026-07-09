import { SectionCard } from "@/components/shared/section-card";
import { providerUsageHistory } from "@/features/providers/mock-data";

export function VerificationProviderUsageCard() {
  return (
    <SectionCard
      title="Sandbox usage"
      description="Mock and sandbox usage while evaluating this provider."
    >
      <div className="space-y-3">
        {providerUsageHistory.map((item) => (
          <div key={item.month} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div>
              <p className="text-sm font-medium text-slate-950">{item.month}</p>
              <p className="mt-1 text-xs text-slate-500">{item.volume} checks</p>
            </div>
            <p className="text-sm font-semibold text-slate-950">{item.spend}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}