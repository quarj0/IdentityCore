import { Button } from "@identitycore/ui";
import { ActivityList } from "@/components/dashboard/activity-list";
import { MetricCard } from "@/components/dashboard/metric-card";
import { OnboardingProgress } from "@/components/dashboard/onboarding-progress";
import { TierStatusCard } from "@/components/dashboard/tier-status-card";
import { PageHeading } from "@/components/shared/page-heading";
import { metrics, workspace } from "@/data/mock-dashboard";
import { NotificationsPanel } from "@/components/notifications/notifications-panel";

export default function DashboardHomePage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title={`Welcome, ${workspace.organizationName}`}
        description="Manage your identity workflows, provider configuration, API access, onboarding, and production readiness."
        action={<Button className="rounded-xl">Create workflow</Button>}
      />

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.65fr_0.35fr]">
        <OnboardingProgress />

        <div className="grid gap-6">
          <TierStatusCard />
          <ActivityList />
          <NotificationsPanel />
        </div>
      </div>
    </div>
  );
}
