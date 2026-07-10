import { ShieldAlert } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Danger zone"
      description="Destructive workspace operations are hidden until server-side controls exist."
      emptyTitle="No destructive actions are available"
      emptyDescription="This avoids showing buttons that cannot safely execute against real tenant APIs."
      icon={ShieldAlert}
    />
  );
}
