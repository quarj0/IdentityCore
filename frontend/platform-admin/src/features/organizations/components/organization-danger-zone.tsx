import { Trash2 } from "lucide-react";
import { Button } from "@identitycore/ui";
import type { Organization } from "@/features/organizations/mock-data";
import { ReactivateOrganizationDialog } from "../forms/reactivate-oraginzation-dialog"; 
import { SuspendOrganizationDialog } from "@/features/organizations/forms/suspend-organization-dialog";

type OrganizationDangerZoneProps = {
  organization: Organization;
};

export function OrganizationDangerZone({
  organization,
}: OrganizationDangerZoneProps) {
  return (
    <section className="rounded-2xl border border-rose-300/20 bg-rose-400/10 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-rose-100">
            Organization controls
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-rose-100/75">
            Suspend, reactivate or delete this organization. These actions are
            platform-wide and should only be used after compliance, support or
            security review.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {organization.status === "suspended" ? (
            <ReactivateOrganizationDialog
              organizationName={organization.name}
            />
          ) : (
            <SuspendOrganizationDialog organizationName={organization.name} />
          )}

          <Button
            variant="destructive"
            className="bg-rose-500 text-white hover:bg-rose-400"
          >
            <Trash2 className="mr-2 size-4" aria-hidden="true" />
            Delete
          </Button>
        </div>
      </div>
    </section>
  );
}
