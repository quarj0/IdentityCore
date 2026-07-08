import { ConfirmationCard } from "@/components/dashboard-ui/confirmation-card";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Danger zone"
        description="Destructive workspace actions require careful confirmation."
      />
      <ConfirmationCard
        title="Delete workspace"
        description="Deleting this workspace will remove configuration and access. This cannot be undone."
        actionLabel="Delete workspace"
      />
    </div>
  );
}
