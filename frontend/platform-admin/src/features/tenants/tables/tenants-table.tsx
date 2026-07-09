import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { Tenant } from "@/features/tenants/mock-data";
import { TenantStatusPill } from "@/features/tenants/components/tenant-status-pill";

type TenantsTableProps = {
  tenants: Tenant[];
};

export function TenantsTable({ tenants }: TenantsTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full min-w-275 text-left text-sm">
          <thead className="border-b border-slate-200 bg-white/2 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">
                Tenant
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Status
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Organization
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Region
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Isolation
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Database
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Latency
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Uptime
              </th>
              <th scope="col" className="px-5 py-4 text-right font-medium">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-white/10">
            {tenants.map((tenant) => (
              <tr key={tenant.id} className="transition hover:bg-white/2">
                <td className="px-5 py-4">
                  <div>
                    <Link
                      href={`/tenants/${tenant.id}`}
                      className="font-medium text-white outline-none hover:text-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-300"
                    >
                      {tenant.name}
                    </Link>
                    <p className="mt-1 text-xs text-slate-500">
                      {tenant.slug} · {tenant.environment}
                    </p>
                  </div>
                </td>

                <td className="px-5 py-4">
                  <TenantStatusPill status={tenant.status} />
                </td>

                <td className="px-5 py-4">
                  <Link
                    href={`/organizations/${tenant.organizationId}`}
                    className="text-slate-300 outline-none hover:text-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-300"
                  >
                    {tenant.organizationName}
                  </Link>
                </td>

                <td className="px-5 py-4 text-slate-300">{tenant.region}</td>

                <td className="px-5 py-4 capitalize text-slate-300">
                  {tenant.isolationModel}
                </td>

                <td className="px-5 py-4">
                  <div>
                    <p className="text-slate-300">{tenant.databaseName}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {tenant.databaseStatus}
                    </p>
                  </div>
                </td>

                <td className="px-5 py-4 text-slate-300">
                  {tenant.apiLatencyMs > 0
                    ? `${tenant.apiLatencyMs}ms`
                    : "Paused"}
                </td>

                <td className="px-5 py-4 text-slate-300">{tenant.uptime}</td>

                <td className="px-5 py-4 text-right">
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
                  >
                    <Link href={`/tenants/${tenant.id}`}>View</Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
