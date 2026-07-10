import { Workflow } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Workflow history"
      description="Workflow history will be connected when workflow APIs are available."
      emptyTitle="No workflow history API is available yet"
      emptyDescription="Current live versioning is handled through verification templates and policy lifecycle events."
      icon={Workflow}
    />
  );
}
