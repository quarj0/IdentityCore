import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import type { Tenant } from "@/features/tenants/mock-data";
import { tenantDatabaseReplicas } from "@/features/tenants/mock-data";

type TenantDatabaseCardProps = {
  tenant: Tenant;
};

export function TenantDatabaseCard({ tenant }: TenantDatabaseCardProps) {
  return (
    <SectionCard
      title="Database"
      description="Database allocation, replica status, migrations and recovery."
      action={
        <StatusPill
          tone={tenant.databaseStatus === "Healthy" ? "success" : "warning"}
        >
          {tenant.databaseStatus}
        </StatusPill>
      }
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-500">Database</p>
          <p className="mt-2 font-medium text-white">{tenant.databaseName}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-500">Isolation model</p>
          <p className="mt-2 font-medium capitalize text-white">
            {tenant.isolationModel}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {tenantDatabaseReplicas.map((replica) => (
          <div
            key={replica.name}
            className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-950/40 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-white">{replica.name}</p>
              <p className="mt-1 text-xs text-slate-500">{replica.region}</p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <StatusPill tone="success">{replica.status}</StatusPill>
              <span className="text-xs text-slate-500">
                Lag {replica.replicationLag}
              </span>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
