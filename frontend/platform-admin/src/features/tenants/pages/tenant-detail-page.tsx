import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { TenantDatabaseCard } from "@/features/tenants/components/tenant-database-card";
import { TenantHealthCard } from "@/features/tenants/components/tenant-health-card";
import { TenantHeader } from "@/features/tenants/components/tenant-header";
import { TenantIsolationCard } from "@/features/tenants/components/tenant-isolation-card";
import { TenantRegionCard } from "@/features/tenants/components/tenant-region-card";
import { TenantStorageCard } from "@/features/tenants/components/tenant-storage-card";
import { TenantSummaryCards } from "@/features/tenants/components/tenant-summary-cards";
import { getTenantById } from "@/features/tenants/mock-data";

type TenantDetailPageProps = {
  tenantId: string;
};

export function TenantDetailPage({ tenantId }: TenantDetailPageProps) {
  const tenant = getTenantById(tenantId);

  if (!tenant) {
    return (
      <EmptyState
        title="Tenant not found"
        description="The tenant may have been deleted, moved to another region, or not provisioned in this environment."
      />
    );
  }

  return (
    <div className="space-y-6">
      <nav
        aria-label="Breadcrumb"
        className="flex items-center gap-2 text-sm text-slate-500"
      >
        <Link
          href="/tenants"
          className="outline-none hover:text-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-300"
        >
          Tenants
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-300">{tenant.name}</span>
      </nav>

      <TenantHeader tenant={tenant} />

      <TenantSummaryCards tenant={tenant} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <TenantHealthCard tenant={tenant} />
          <TenantDatabaseCard tenant={tenant} />
          <TenantIsolationCard tenant={tenant} />
        </div>

        <div className="space-y-4">
          <TenantRegionCard tenant={tenant} />
          <TenantStorageCard tenant={tenant} />
        </div>
      </div>
    </div>
  );
}
