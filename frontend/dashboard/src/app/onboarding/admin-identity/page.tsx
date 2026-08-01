import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { AdminIdentityPanel } from "@/components/onboarding/admin-identity-panel";

export default function AdminIdentityPage() {
  return (
    <OnboardingPageShell
      eyebrow="Administrator identity"
      title="Verify the workspace administrator."
      description="The primary administrator must verify their identity before the organization can request production access."
      pathname="/onboarding/admin-identity"
    >
      <AdminIdentityPanel />
    </OnboardingPageShell>
  );
}
