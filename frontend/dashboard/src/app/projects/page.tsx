import { Building2 } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function ProjectsPage() {
  return (
    <NoBackendModulePage
      title="Projects"
      description="Project management will be connected when project APIs are available."
      emptyTitle="No project API is available yet"
      emptyDescription="Verification requests, templates, API keys, webhooks, and audit logs are already live. Project grouping remains outside this delivery."
      icon={Building2}
    />
  );
}
