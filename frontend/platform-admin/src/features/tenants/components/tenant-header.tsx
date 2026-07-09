import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { Tenant } from "@/features/tenants/mock-data";
import { TenantMaintenanceDialog } from "@/features/tenants/forms/tenant-maintenance-dialog";
import { TenantStatusPill } from "@/features/tenants/components/tenant-status-pill";

type TenantHeaderProps = {
  tenant: Tenant;
};

export function TenantHeader({ tenant }: TenantHeaderProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-white">
              {tenant.name}
            </h1>
            <TenantStatusPill status={tenant.status} />
          </div>

          <p className="mt-2 text-sm text-slate-500">
            Tenant for{" "}
            <Link
              href={`/organizations/${tenant.organizationId}`}
              className="text-cyan-300 outline-none hover:text-cyan-200 focus-visible:ring-2 focus-visible:ring-cyan-300"
            >
              {tenant.organizationName}
            </Link>{" "}
            · {tenant.region} · {tenant.environment}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-3">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">
                Isolation
              </dt>
              <dd className="mt-1 text-sm font-medium capitalize text-white">
                {tenant.isolationModel}
              </dd>
            </div>

            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">
                Database
              </dt>
              <dd className="mt-1 text-sm font-medium text-white">
                {tenant.databaseName}
              </dd>
            </div>

            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">
                Created
              </dt>
              <dd className="mt-1 text-sm font-medium text-white">
                {tenant.createdAt}
              </dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
          >
            View logs
          </Button>

          <Button
            variant="outline"
            className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
          >
            Run health check
          </Button>

          <TenantMaintenanceDialog tenantName={tenant.name} />
        </div>
      </div>
    </section>
  );
}
