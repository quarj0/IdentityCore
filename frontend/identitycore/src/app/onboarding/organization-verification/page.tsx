import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { OrganizationVerificationForm } from "@/components/onboarding/organization-verification-form";

export default function OrganizationVerificationPage() {
  return (
    <OnboardingPageShell
      eyebrow="Organization verification"
      title="Verify your organization."
      description="Upload documents that prove your organization is legitimate before production access is approved."
      pathname="/onboarding/organization-verification"
    >
      <OrganizationVerificationForm />
    </OnboardingPageShell>
  );
}
