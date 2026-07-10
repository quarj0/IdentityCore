import { Settings } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function ProjectSettingsPage() {
  return (
    <NoBackendModulePage
      title="Project settings"
      description="Project settings will be connected when project APIs are available."
      emptyTitle="No project settings API is available yet"
      emptyDescription="This page intentionally shows no sample configuration."
      icon={Settings}
    />
  );
}
