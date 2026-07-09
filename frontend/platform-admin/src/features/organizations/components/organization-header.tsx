import { Button } from "@identitycore/ui";
import type { Organization } from "@/features/organizations/mock-data";
import { OrganizationRiskScore } from "@/features/organizations/components/organization-risk-score";
import { OrganizationStatusPill } from "@/features/organizations/components/organization-status-pill";

type OrganizationHeaderProps = {
  organization: Organization;
};

export function OrganizationHeader({ organization }: OrganizationHeaderProps) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/3 p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-4">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-cyan-400/10 text-lg font-semibold text-cyan-300 ring-1 ring-cyan-300/20">
            {organization.logoInitials}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-white">
                {organization.name}
              </h1>

              <OrganizationStatusPill status={organization.status} />
            </div>

            <p className="mt-2 text-sm text-slate-400">
              {organization.industry} · {organization.country} ·{" "}
              {organization.region}
            </p>

            <div className="mt-4">
              <OrganizationRiskScore
                score={organization.riskScore}
                level={organization.riskLevel}
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="border-white/10 bg-white/5 text-slate-200 hover:bg-white/10"
          >
            View audit trail
          </Button>

          <Button
            variant="outline"
            className="border-white/10 bg-white/5 text-slate-200 hover:bg-white/10"
          >
            Impersonate
          </Button>

          <Button>Open workspace</Button>
        </div>
      </div>
    </section>
  );
}
