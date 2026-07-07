import Link from "next/link";
import { ArrowRight, Fingerprint } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function AdminIdentityPage() {
  return (
    <OnboardingPageShell
      eyebrow="Administrator identity"
      title="Verify the workspace administrator."
      description="The primary administrator must verify their identity before the organization can request production access."
      pathname="/onboarding/admin-identity"
    >
      <Card className="max-w-2xl rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <Fingerprint className="mb-4 h-7 w-7 text-blue-600" />
          <CardTitle>Identity verification required</CardTitle>
          <CardDescription className="leading-7">
            You will complete a secure IdentityCore verification flow using an
            identity document, selfie, and optional liveness check.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Button asChild size="lg" className="w-full rounded-xl sm:w-auto">
            <Link href="/onboarding/admin-identity/start">
              Start verification
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </OnboardingPageShell>
  );
}
