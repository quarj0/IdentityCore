import { Workflow } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Workflow"
      description="Workflow detail will be connected when workflow APIs are available."
      emptyTitle="No workflow detail API is available yet"
      emptyDescription="Use Templates for live verification policy management in this version."
      icon={Workflow}
    />
  );
}
