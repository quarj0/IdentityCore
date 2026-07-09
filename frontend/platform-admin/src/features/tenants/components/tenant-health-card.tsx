import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import type { Tenant } from "@/features/tenants/mock-data";
import { tenantHealthEvents } from "@/features/tenants/mock-data";

type TenantHealthCardProps = {
  tenant: Tenant;
};

type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";

function getHealthTone(status: string): StatusTone {
  if (status === "healthy") return "success";

  if (
    status === "degraded" ||
    status === "maintenance" ||
    status === "provisioning"
  ) {
    return "warning";
  }

  return "danger";
}

function getEventTone(severity: string): StatusTone {
  if (severity === "Success") return "success";
  if (severity === "Warning") return "warning";
  if (severity === "Info") return "info";

  return "neutral";
}

export function TenantHealthCard({ tenant }: TenantHealthCardProps) {
  return (
    <SectionCard
      title="Tenant health"
      description="Live tenant status, recent health checks and operational events."
      action={
        <StatusPill tone={getHealthTone(tenant.status)}>
          {tenant.status}
        </StatusPill>
      }
    >
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">Last health check</p>
          <p className="mt-2 font-medium text-white">
            {tenant.lastHealthCheckAt}
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">Uptime</p>
          <p className="mt-2 font-medium text-white">{tenant.uptime}</p>
        </div>

        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">p95 latency</p>
          <p className="mt-2 font-medium text-white">
            {tenant.apiLatencyMs > 0 ? `${tenant.apiLatencyMs}ms` : "Paused"}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {tenantHealthEvents.map((event) => (
          <div
            key={event.title}
            className="rounded-xl border border-white/10 bg-slate-950/40 p-4"
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-white">{event.title}</p>
                <p className="mt-1 text-sm text-slate-400">
                  {event.description}
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <StatusPill tone={getEventTone(event.severity)}>
                  {event.severity}
                </StatusPill>
                <span className="text-xs text-slate-500">{event.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
