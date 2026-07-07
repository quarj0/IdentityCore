import Link from "next/link";
import { ArrowRight, Check, Fingerprint, ShieldCheck } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Checkbox,
  Label,
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
      <div className="grid gap-6 lg:grid-cols-[1fr_0.42fr]">
        <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
          <CardHeader>
            <Fingerprint className="mb-4 h-7 w-7 text-blue-600" />
            <CardTitle>Administrator verification</CardTitle>
            <CardDescription className="leading-7">
              You will complete a short verification flow using an identity
              document, selfie capture, liveness check, and mock AI result.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-medium">Before you continue</p>

              <div className="mt-4 space-y-3">
                {[
                  "Use your own identity document.",
                  "Make sure your document is clear and readable.",
                  "Use good lighting for selfie capture.",
                  "This demo currently produces mock verification results.",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex gap-3 text-sm leading-6 text-muted-foreground"
                  >
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4">
              <Checkbox id="consent" className="mt-1" />
              <Label
                htmlFor="consent"
                className="text-sm leading-6 text-muted-foreground"
              >
                I consent to IdentityCore processing my administrator identity
                evidence for workspace onboarding and production approval.
              </Label>
            </div>

            <Button asChild size="lg" className="rounded-xl">
              <Link href="/verification">
                Launch verification
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
          <CardHeader>
            <ShieldCheck className="mb-4 h-6 w-6 text-blue-600" />
            <CardTitle>Verification flow</CardTitle>
            <CardDescription className="leading-7">
              Consent, document capture, selfie capture, liveness check,
              processing, and result.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </OnboardingPageShell>
  );
}
