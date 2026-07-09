import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import { organizationDomains } from "@/features/organizations/mock-data";

export function OrganizationDomainsCard() {
  return (
    <SectionCard
      title="Domains"
      description="Custom domains, SSL status and verification endpoints."
    >
      <div className="space-y-3">
        {organizationDomains.map((domain) => (
          <div
            key={domain.domain}
            className="rounded-xl border border-slate-200 bg-slate-950/40 p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-white">
                  {domain.domain}
                </p>
                <p className="mt-1 text-xs text-slate-500">{domain.type}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <StatusPill
                  tone={domain.status === "Verified" ? "success" : "warning"}
                >
                  {domain.status}
                </StatusPill>

                <StatusPill
                  tone={domain.ssl === "Active" ? "success" : "warning"}
                >
                  {`SSL ${domain.ssl}`}
                </StatusPill>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
