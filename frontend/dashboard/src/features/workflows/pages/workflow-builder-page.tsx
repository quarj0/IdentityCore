import { WorkflowBuilderCanvas } from "../components/workflow-builder-canvas";
import { WorkflowSettingsPanel } from "../components/workflow-settings-panel";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export function WorkflowBuilderPage() {
  return (
    <ResourceDetailLayout
      backHref="/workflows"
      backLabel="Back to workflows"
      title="Workflow builder"
      description="Build identity workflows using steps, policies, provider routing, and decision nodes."
      status="Draft"
    >
      <div className="grid gap-6 xl:grid-cols-[0.7fr_0.3fr]">
        <WorkflowBuilderCanvas />
        <WorkflowSettingsPanel />
      </div>
    </ResourceDetailLayout>
  );
}
