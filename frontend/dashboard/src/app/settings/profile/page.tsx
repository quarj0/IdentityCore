import { User } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Profile"
      description="Profile editing will be connected when account update APIs are available."
      emptyTitle="Profile editing is not available yet"
      emptyDescription="The dashboard currently reads your account through the authenticated /auth/me endpoint."
      icon={User}
    />
  );
}
