import { SectionCard } from "@/components/shared/section-card";
import { organizationUsage } from "@/features/organizations/mock-data";

function UsageBar({
  label,
  used,
  limit,
  suffix = "",
}: {
  label: string;
  used: number;
  limit: number;
  suffix?: string;
}) {
  const percentage = Math.round((used / limit) * 100);

  return (
    <div>
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="font-medium text-slate-200">{label}</span>
        <span className="text-slate-400">
          {used.toLocaleString()}
          {suffix} / {limit.toLocaleString()}
          {suffix}
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
  );
}

export function OrganizationUsageCard() {
  return (
    <SectionCard
      title="Usage"
      description="Monthly quota, API consumption, storage and configuration usage."
    >
      <div className="space-y-5">
        <UsageBar
          label="Verifications"
          used={organizationUsage.verificationsUsed}
          limit={organizationUsage.verificationsLimit}
        />

        <UsageBar
          label="API requests"
          used={organizationUsage.apiUsed}
          limit={organizationUsage.apiLimit}
        />

        <UsageBar
          label="Evidence storage"
          used={organizationUsage.storageUsedGb}
          limit={organizationUsage.storageLimitGb}
          suffix="GB"
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
            <p className="text-sm text-slate-400">Reviewers</p>
            <p className="mt-2 text-xl font-semibold text-white">
              {organizationUsage.reviewers}
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
            <p className="text-sm text-slate-400">Templates</p>
            <p className="mt-2 text-xl font-semibold text-white">
              {organizationUsage.templates}
            </p>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
