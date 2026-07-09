import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import { systemStatus } from "@/features/dashboard/mock-data";

export function SystemStatusCard() {
  return (
    <SectionCard
      title="System status"
      description="Live health summary across IdentityCore platform services."
    >
      <div className="space-y-3">
        {systemStatus.map((service) => (
          <div
            key={service.name}
            className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-slate-950/40 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-white">{service.name}</p>
              <p className="mt-1 text-xs text-slate-500">{service.region}</p>
            </div>

            <StatusPill
              tone={service.status === "Operational" ? "success" : "warning"}
            >
              {service.status}
            </StatusPill>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
