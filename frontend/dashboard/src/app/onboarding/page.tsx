import { OnboardingProgress } from "@/components/dashboard/onboarding-progress";
import { TierStatusCard } from "@/components/dashboard/tier-status-card";
import { PageHeading } from "@/components/shared/page-heading";

export default function OnboardingPage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Workspace onboarding"
        description="Complete organization setup, verification, first workflow, and production approval."
      />

      <div className="grid gap-6 xl:grid-cols-[0.65fr_0.35fr]">
        <OnboardingProgress />
        <TierStatusCard />
      </div>
    </div>
  );
}
