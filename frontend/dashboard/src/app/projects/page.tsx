import { Building2 } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables"; 

export default function ProjectsPage() {
  return (
    <ResourcePage
      title="Projects"
      description="Manage sandbox and production projects for your organization."
      actionLabel="Create project"
      emptyTitle="No projects yet"
      emptyDescription="Create a project to organize workflows, keys, and environments."
      icon={Building2}
      {...tableData.projects}
    />
  );
}
