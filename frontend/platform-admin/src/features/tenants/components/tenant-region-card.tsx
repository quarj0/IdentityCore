import { Globe2 } from "lucide-react";
import { SectionCard } from "@/components/shared/section-card";
import type { Tenant } from "@/features/tenants/mock-data";

type TenantRegionCardProps = {
  tenant: Tenant;
};

export function TenantRegionCard({ tenant }: TenantRegionCardProps) {
  const items = [
    {
      label: "Primary region",
      value: tenant.region,
    },
    {
      label: "Environment",
      value: tenant.environment,
    },
    {
      label: "Data residency",
      value: tenant.region.includes("Africa")
        ? "Africa boundary"
        : "Regional boundary",
    },
    {
      label: "Failover policy",
      value:
        tenant.isolationModel === "dedicated"
          ? "Dedicated DR"
          : "Shared regional DR",
    },
  ];

  return (
    <SectionCard
      title="Region"
      description="Tenant location, residency boundary and failover policy."
    >
      <div className="mb-4 flex items-center gap-3 rounded-xl border border-cyan-300/20 bg-cyan-400/10 p-4 text-cyan-100">
        <Globe2 className="size-5 text-cyan-300" aria-hidden="true" />
        <p className="text-sm">
          This tenant is currently hosted in{" "}
          <span className="font-semibold">{tenant.region}</span>.
        </p>
      </div>

      <dl className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-white/10 bg-slate-950/40 p-4"
          >
            <dt className="text-sm text-slate-400">{item.label}</dt>
            <dd className="mt-2 font-medium capitalize text-white">
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
    </SectionCard>
  );
}
