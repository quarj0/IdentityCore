import { MockVerificationFlow } from "@/components/verification/mock-verification-flow";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function VerificationPage() {
  return (
    <OnboardingPageShell
      eyebrow="Verification"
      title="Complete administrator verification."
      description="This mock flow previews document capture, selfie capture, liveness, processing, and verification results."
      pathname="/onboarding/admin-identity"
    >
      <MockVerificationFlow />
    </OnboardingPageShell>
  );
}
