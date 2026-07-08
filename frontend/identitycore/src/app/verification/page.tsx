import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { VerificationSessionFlow } from "@/components/verification/verification-session-flow";

export default async function VerificationPage({
  searchParams,
}: {
  searchParams: Promise<{
    sessionId?: string;
    token?: string;
    verificationId?: string;
  }>;
}) {
  const params = await searchParams;

  return (
    <OnboardingPageShell
      eyebrow="Verification"
      title="Complete administrator verification."
      description="Complete the live administrator identity flow for onboarding."
      pathname="/onboarding/admin-identity"
    >
      <VerificationSessionFlow
        sessionId={params.sessionId}
        sessionToken={params.token}
        verificationId={params.verificationId}
      />
    </OnboardingPageShell>
  );
}
