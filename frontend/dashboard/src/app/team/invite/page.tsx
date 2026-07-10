import { UserPlus } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function Page() {
  return (
    <NoBackendModulePage
      title="Team invitations"
      description="Team membership is shown from the live tenant API. Invitation creation still needs a backend invitation endpoint, so this page no longer presents a pretend send flow."
      emptyTitle="Team invitations are not connected yet"
      emptyDescription="The dashboard now reads real team members from the backend. Once invitation APIs exist, this page can send actual invitations instead of a fake form."
      icon={UserPlus}
    />
  );
}
