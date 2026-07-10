import { Workflow } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function WorkflowsPage() {
  return (
    <NoBackendModulePage
      title="Workflows"
      description="Workflow-builder APIs are not available yet. Active verification templates are currently managed as policies."
      emptyTitle="No workflow API is available yet"
      emptyDescription="Use Templates to manage verification policy versions for now."
      icon={Workflow}
    />
  );
}
