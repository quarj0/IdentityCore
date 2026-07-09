import { LockKeyhole } from "lucide-react";
import { SectionCard } from "@/components/shared/section-card";
import type { Tenant } from "@/features/tenants/mock-data";
import { tenantIsolationControls } from "@/features/tenants/mock-data";

type TenantIsolationCardProps = {
  tenant: Tenant;
};

export function TenantIsolationCard({ tenant }: TenantIsolationCardProps) {
  return (
    <SectionCard
      title="Isolation"
      description="Data, compute, access and network separation controls."
    >
      <div className="mb-4 flex items-center gap-3 rounded-xl border border-emerald-300/20 bg-emerald-400/10 p-4 text-emerald-100">
        <LockKeyhole className="size-5 text-emerald-300" aria-hidden="true" />
        <p className="text-sm">
          This tenant uses{" "}
          <span className="font-semibold capitalize">
            {tenant.isolationModel}
          </span>{" "}
          isolation.
        </p>
      </div>

      <div className="space-y-3">
        {tenantIsolationControls.map((control) => (
          <div
            key={control.label}
            className="rounded-xl border border-slate-200 bg-slate-950/40 p-4"
          >
            <p className="text-sm text-slate-500">{control.label}</p>
            <p className="mt-2 text-sm font-medium leading-6 text-white">
              {control.value}
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
