import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { OrganizationBrandingCard } from "@/features/organizations/components/organization-branding-card";
import { OrganizationDangerZone } from "@/features/organizations/components/organization-danger-zone";
import { OrganizationDomainsCard } from "@/features/organizations/components/organization-domains-card";
import { OrganizationHeader } from "@/features/organizations/components/organization-header";
import { OrganizationSubscriptionCard } from "../components/organization-subcription-card"; 
import { OrganizationSummaryCards } from "@/features/organizations/components/organization-summary-cards";
import { OrganizationUsageCard } from "@/features/organizations/components/organization-usage-card";
import { organizations } from "@/features/organizations/mock-data";

type OrganizationDetailPageProps = {
  organizationId: string;
};

export function OrganizationDetailPage({
  organizationId,
}: OrganizationDetailPageProps) {
  const organization = organizations.find((item) => item.id === organizationId);

  if (!organization) {
    return (
      <EmptyState
        title="Organization not found"
        description="The organization may have been deleted, archived or moved to another environment."
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
          href="/organizations"
          className="outline-none hover:text-cyan-300 focus-visible:ring-2 focus-visible:ring-cyan-300"
        >
          Organizations
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-300">{organization.name}</span>
      </nav>

      <OrganizationHeader organization={organization} />

      <OrganizationSummaryCards organization={organization} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <OrganizationUsageCard />
          <OrganizationDomainsCard />
          <OrganizationDangerZone organization={organization} />
        </div>

        <div className="space-y-4">
          <OrganizationSubscriptionCard />
          <OrganizationBrandingCard />
        </div>
      </div>
    </div>
  );
}
