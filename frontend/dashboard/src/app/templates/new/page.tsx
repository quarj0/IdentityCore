import { PageHeading } from "@/components/shared/page-heading";
import { ProjectForm } from "@/components/forms/project-form";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Create template"
        description="Create a reusable workflow template for your organization."
      />
      <ProjectForm />
    </div>
  );
}