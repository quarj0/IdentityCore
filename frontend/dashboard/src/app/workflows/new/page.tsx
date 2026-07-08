import { WorkflowBuilderCanvas } from "@/features/workflows/components/workflow-builder-canvas";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Create workflow"
        description="Start a new workflow from scratch or clone a template."
      />
      <WorkflowBuilderCanvas />
    </div>
  );
}
