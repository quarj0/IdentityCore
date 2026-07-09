import { Activity, Calendar, CreditCard, Globe2 } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import type { Organization } from "@/features/organizations/mock-data";

type OrganizationSummaryCardsProps = {
  organization: Organization;
};

export function OrganizationSummaryCards({
  organization,
}: OrganizationSummaryCardsProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Verifications this month"
        value={organization.verificationsThisMonth.toLocaleString()}
        change="+11.2%"
        trend="up"
        helperText="30 days"
        icon={Activity}
      />

      <MetricCard
        label="API requests"
        value={organization.apiRequestsThisMonth.toLocaleString()}
        change="+8.4%"
        trend="up"
        helperText="30 days"
        icon={Globe2}
      />

      <MetricCard
        label="Monthly spend"
        value={organization.monthlySpend}
        change="+14.1%"
        trend="up"
        helperText="MRR"
        icon={CreditCard}
      />

      <MetricCard
        label="Created"
        value={organization.createdAt}
        change="Verified"
        trend="neutral"
        helperText="onboarding"
        icon={Calendar}
      />
    </section>
  );
}
