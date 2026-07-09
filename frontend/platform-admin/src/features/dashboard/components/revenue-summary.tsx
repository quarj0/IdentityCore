import { SectionCard } from "@/components/shared/section-card";
import { revenueSummary } from "@/features/dashboard/mock-data";

export function RevenueSummary() {
  const items = [
    {
      label: "Monthly recurring revenue",
      value: revenueSummary.mrr,
    },
    {
      label: "Usage revenue",
      value: revenueSummary.usageRevenue,
    },
    {
      label: "Platform fees",
      value: revenueSummary.platformFees,
    },
    {
      label: "Overdue invoices",
      value: revenueSummary.overdueInvoices,
    },
  ];

  return (
    <SectionCard
      title="Revenue summary"
      description="Platform-wide billing and revenue snapshot."
    >
      <dl className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-white/10 bg-slate-950/40 p-4"
          >
            <dt className="text-sm text-slate-400">{item.label}</dt>
            <dd className="mt-2 text-xl font-semibold text-white">
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
    </SectionCard>
  );
}
