import { ListChecks } from "lucide-react";
import { NoBackendModulePage } from "@/features/operations/no-backend-module-page";

export default function OnboardingPage() {
  return (
    <NoBackendModulePage
      title="Workspace onboarding"
      description="Workspace onboarding is managed by the live organization onboarding flow."
      emptyTitle="No dashboard onboarding tasks are available"
      emptyDescription="Use the organization onboarding screens to complete email, administrator identity, organization verification, and production approval."
      icon={ListChecks}
    />
  );
}
