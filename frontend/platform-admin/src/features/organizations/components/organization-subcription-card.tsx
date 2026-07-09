import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import { organizationSubscription } from "@/features/organizations/mock-data";

export function OrganizationSubscriptionCard() {
  const items = [
    {
      label: "Plan",
      value: organizationSubscription.plan,
    },
    {
      label: "Billing cycle",
      value: organizationSubscription.billingCycle,
    },
    {
      label: "Renewal date",
      value: organizationSubscription.renewalDate,
    },
    {
      label: "Current usage cost",
      value: organizationSubscription.currentUsageCost,
    },
    {
      label: "Base fee",
      value: organizationSubscription.baseFee,
    },
    {
      label: "Usage fee",
      value: organizationSubscription.usageFee,
    },
  ];

  return (
    <SectionCard
      title="Subscription"
      description="Plan, billing cycle, renewal and monthly charges."
      action={
        <StatusPill tone="success">
          {organizationSubscription.paymentStatus}
        </StatusPill>
      }
    >
      <dl className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-white/10 bg-slate-950/40 p-4"
          >
            <dt className="text-sm text-slate-400">{item.label}</dt>
            <dd className="mt-2 font-medium text-white">{item.value}</dd>
          </div>
        ))}
      </dl>
    </SectionCard>
  );
}
