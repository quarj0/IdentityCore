import { ConfirmationCard } from "@/components/dashboard-ui/confirmation-card";
import { ProjectForm } from "@/components/forms/project-form";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export default function ProjectSettingsPage() {
  return (
    <ResourceDetailLayout
      backHref="/projects"
      backLabel="Back to projects"
      title="Project settings"
      description="Manage project configuration, environment, and danger zone."
      status="Sandbox"
    >
      <div className="space-y-6">
        <ProjectForm />
        <ConfirmationCard
          title="Delete project"
          description="Deleting this project will remove related configuration. This cannot be undone."
          actionLabel="Delete project"
        />
      </div>
    </ResourceDetailLayout>
  );
}
