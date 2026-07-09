import { SectionCard } from "@/components/shared/section-card";
import type { Tenant } from "@/features/tenants/mock-data";

type TenantStorageCardProps = {
  tenant: Tenant;
};

export function TenantStorageCard({ tenant }: TenantStorageCardProps) {
  const percentage = Math.round(
    (tenant.storageUsedGb / tenant.storageLimitGb) * 100,
  );

  return (
    <SectionCard
      title="Storage"
      description="Evidence storage usage, bucket assignment and retention readiness."
    >
      <div>
        <div className="flex items-center justify-between gap-4 text-sm">
          <span className="font-medium text-slate-200">Evidence storage</span>
          <span className="text-slate-400">
            {tenant.storageUsedGb}GB / {tenant.storageLimitGb}GB
          </span>
        </div>

        <div className="mt-2 h-2 rounded-full bg-white/10">
          <div
            className="h-2 rounded-full bg-cyan-300"
            style={{ width: `${percentage}%` }}
          />
        </div>

        <p className="mt-1 text-xs text-slate-500">{percentage}% used</p>
      </div>

      <div className="mt-5 space-y-3">
        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">Storage bucket</p>
          <p className="mt-2 break-all font-medium text-white">
            {tenant.storageBucket}
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">Retention policy</p>
          <p className="mt-2 font-medium text-white">
            Organization-configured, platform-enforced
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-400">Encryption</p>
          <p className="mt-2 font-medium text-white">
            Server-side encryption with tenant-scoped keys
          </p>
        </div>
      </div>
    </SectionCard>
  );
}
