import { Bell } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Notification settings"
      description="Notification preferences will be connected when preference APIs are available."
      emptyTitle="Notification preferences are not available yet"
      emptyDescription="Live notification delivery records are available from the Notifications page."
      icon={Bell}
    />
  );
}
