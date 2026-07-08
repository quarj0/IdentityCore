import { Workflow } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { OrganizationSettingsForm } from "@/components/settings/organization-settings-form";

export default function WorkflowsPage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Workflows"
        description="Build, configure, and publish identity workflows for your organization."
      />

      <EmptyState
        icon={Workflow}
        title="No workflows yet"
        description="Create your first workflow from scratch or clone an official template."
        actionLabel="Create workflow"
          />
          <OrganizationSettingsForm />
    </div>
  );
}