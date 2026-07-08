import { ProjectIntegrations } from "../components/project-integrations";
import { ProjectOverview } from "../components/project-overview";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export function ProjectDetailPage({ id }: { id: string }) {
  return (
    <ResourceDetailLayout
      backHref="/projects"
      backLabel="Back to projects"
      title="Default Sandbox"
      description={`Project ID: ${id}`}
      status="Active"
    >
      <div className="grid gap-6 xl:grid-cols-[0.6fr_0.4fr]">
        <ProjectOverview />
        <ProjectIntegrations />
      </div>
    </ResourceDetailLayout>
  );
}
