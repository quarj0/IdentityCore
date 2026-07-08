import { PageHeading } from "@/components/shared/page-heading";
import { OrganizationSettingsForm } from "@/components/settings/organization-settings-form";

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Settings"
        description="Configure organization profile, environments, retention, and workspace preferences."
      />

      <OrganizationSettingsForm />
    </div>
  );
}
