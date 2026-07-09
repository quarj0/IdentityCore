import { Activity, Clock3, Database, Users } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import type { Tenant } from "@/features/tenants/mock-data";

type TenantSummaryCardsProps = {
  tenant: Tenant;
};

export function TenantSummaryCards({ tenant }: TenantSummaryCardsProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Verifications today"
        value={tenant.verificationsToday.toLocaleString()}
        change="+7.8%"
        trend={tenant.verificationsToday > 0 ? "up" : "neutral"}
        helperText="24 hours"
        icon={Activity}
      />

      <MetricCard
        label="API latency"
        value={tenant.apiLatencyMs > 0 ? `${tenant.apiLatencyMs}ms` : "Paused"}
        change={
          tenant.apiLatencyMs < 150 && tenant.apiLatencyMs > 0
            ? "Healthy"
            : "Watch"
        }
        trend={
          tenant.apiLatencyMs < 150 && tenant.apiLatencyMs > 0
            ? "up"
            : "neutral"
        }
        helperText="p95"
        icon={Clock3}
      />

      <MetricCard
        label="Active users"
        value={tenant.activeUsers.toLocaleString()}
        change="+3.2%"
        trend={tenant.activeUsers > 0 ? "up" : "neutral"}
        helperText="7 days"
        icon={Users}
      />

      <MetricCard
        label="Database"
        value={tenant.databaseStatus}
        change={tenant.uptime}
        trend={tenant.databaseStatus === "Healthy" ? "up" : "neutral"}
        helperText="uptime"
        icon={Database}
      />
    </section>
  );
}
