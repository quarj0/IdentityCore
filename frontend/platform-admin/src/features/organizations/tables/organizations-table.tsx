import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { Organization } from "@/features/organizations/mock-data";
import { OrganizationActionsMenu } from "@/features/organizations/components/organization-actions-menu";
import { OrganizationRiskScore } from "@/features/organizations/components/organization-risk-score";
import { OrganizationStatusPill } from "@/features/organizations/components/organization-status-pill";

type OrganizationsTableProps = {
  organizations: Organization[];
};

export function OrganizationsTable({ organizations }: OrganizationsTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/3">
      <div className="overflow-x-auto">
        <table className="w-full min-w-275 text-left text-sm">
          <thead className="border-b border-white/10 bg-white/2 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">
                Organization
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Status
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Plan
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Country
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Risk
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Verifications
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Monthly spend
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Last active
              </th>
              <th scope="col" className="px-5 py-4 text-right font-medium">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-white/10">
            {organizations.map((organization) => (
              <tr
                key={organization.id}
                className="transition hover:bg-white/2"
              >
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400/10 text-sm font-semibold text-cyan-300 ring-1 ring-cyan-300/20">
                      {organization.logoInitials}
                    </div>

                    <div>
                      <Link
                        href={`/organizations/${organization.id}`}
                        className="font-medium text-white outline-none hover:text-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-300"
                      >
                        {organization.name}
                      </Link>
                      <p className="mt-1 text-xs text-slate-500">
                        {organization.ownerEmail}
                      </p>
                    </div>
                  </div>
                </td>

                <td className="px-5 py-4">
                  <OrganizationStatusPill status={organization.status} />
                </td>

                <td className="px-5 py-4 capitalize text-slate-300">
                  {organization.plan}
                </td>

                <td className="px-5 py-4 text-slate-300">
                  {organization.country}
                </td>

                <td className="px-5 py-4">
                  <OrganizationRiskScore
                    score={organization.riskScore}
                    level={organization.riskLevel}
                  />
                </td>

                <td className="px-5 py-4 text-slate-300">
                  {organization.verificationsThisMonth.toLocaleString()}
                </td>

                <td className="px-5 py-4 text-slate-300">
                  {organization.monthlySpend}
                </td>

                <td className="px-5 py-4 text-slate-400">
                  {organization.lastActiveAt}
                </td>

                <td className="px-5 py-4 text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      asChild
                      variant="outline"
                      size="sm"
                      className="border-white/10 bg-white/5 text-slate-200 hover:bg-white/10"
                    >
                      <Link href={`/organizations/${organization.id}`}>
                        View
                      </Link>
                    </Button>

                    <OrganizationActionsMenu organization={organization} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
