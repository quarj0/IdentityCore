import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { OrganizationProfilePanel } from "@/components/onboarding/organization-profile-panel";

export default function OrganizationProfilePage() {
  return (
    <OnboardingPageShell
      eyebrow="Organization profile"
      title="Tell us about your organization."
      description="Review the workspace information captured during registration before you move into formal organization verification."
      pathname="/onboarding/organization-profile"
    >
      <OrganizationProfilePanel />
    </OnboardingPageShell>
  );
}
