import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { ProductionApprovalPanel } from "@/components/onboarding/production-approval-panel";

export default function ProductionApprovalPage() {
  return (
    <OnboardingPageShell
      eyebrow="Production approval"
      title="Submit your workspace for production access."
      description="Production access is reviewed to protect IdentityCore, organizations, and verification subjects from abuse."
      pathname="/onboarding/production-approval"
    >
      <ProductionApprovalPanel />
    </OnboardingPageShell>
  );
}
