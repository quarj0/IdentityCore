import { Button } from "@identitycore/ui";
import { PageHeader } from "@/components/shared/page-header";
import { IncidentBanner } from "@/components/feedback/incident-banner";
import { DashboardMetricsGrid } from "@/features/dashboard/components/dashboard-metrics-grid";
import { AiProviderHealth } from "@/features/dashboard/components/ai-provider-health";
import { ApiTrafficCard } from "@/features/dashboard/components/api-traffic-card";
import { RevenueSummary } from "@/features/dashboard/components/revenue-summary";
import { SystemStatusCard } from "@/features/dashboard/components/system-status-card";
import { VerificationActivity } from "@/features/dashboard/components/verification-activity";
import { incident } from "@/features/dashboard/mock-data";

export function PlatformDashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform command center"
        title="Platform Dashboard"
        description="Monitor IdentityCore globally across organizations, tenants, verifications, API traffic, AI provider health, revenue, incidents and system status."
        actions={
          <>
            <Button
              variant="outline"
              className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
            >
              Export report
            </Button>
            <Button>Open command palette</Button>
          </>
        }
      />

      <IncidentBanner
        title={incident.title}
        description={incident.description}
        severity={incident.severity}
      />

      <DashboardMetricsGrid />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <VerificationActivity />
          <ApiTrafficCard />
        </div>

        <div className="space-y-4">
          <AiProviderHealth />
          <SystemStatusCard />
          <RevenueSummary />
        </div>
      </div>
    </div>
  );
}
