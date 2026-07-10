import { Workflow } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Workflow builder"
      description="The workflow builder will be enabled when workflow APIs are available."
      emptyTitle="No workflow builder API is available yet"
      emptyDescription="This page intentionally avoids showing a fake builder."
      icon={Workflow}
    />
  );
}
