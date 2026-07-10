"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Check, Fingerprint, Loader2, ShieldCheck } from "lucide-react";
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
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import {
  createAdministratorOnboardingVerification,
  fetchCurrentOnboarding,
  type OnboardingState,
} from "@/lib/onboarding-api";

export function AdminIdentityPanel() {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentOnboarding()
      .then(setState)
      .catch((error) => {
        setErrorMessage(getErrorMessage(error));
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleLaunch() {
    if (!state) {
      return;
    }

    setLaunching(true);
    setErrorMessage(null);
    try {
      const verification = await createAdministratorOnboardingVerification();
      window.location.assign(verification.verificationUrl);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setLaunching(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.42fr]">
      <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <Fingerprint className="mb-4 h-7 w-7 text-blue-600" />
          <CardTitle>Administrator verification</CardTitle>
          <CardDescription className="leading-7">
            Launch a live administrator identity verification session for{" "}
            {state?.administratorFullName || "the workspace owner"}.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {errorMessage ? (
            <InlineStatus
              kind="error"
              title={
                state ? "Unable to launch verification" : "Unable to load administrator status"
              }
              message={errorMessage}
            />
          ) : null}

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-sm font-medium">Before you continue</p>

            <div className="mt-4 space-y-3">
              {[
                "Use your own identity document.",
                "Make sure the document image is clear and readable.",
                "Upload a clear selfie image from the same person.",
                "The onboarding record will be updated with the verification ID after submission.",
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
            <Checkbox
              id="consent"
              className="mt-1"
              checked={consent}
              onCheckedChange={(checked) => setConsent(Boolean(checked))}
            />
            <Label
              htmlFor="consent"
              className="text-sm leading-6 text-muted-foreground"
            >
              I consent to IdentityCore processing administrator identity evidence
              for workspace onboarding and production approval.
            </Label>
          </div>

          <Button
            size="lg"
            className="rounded-xl"
            onClick={handleLaunch}
            disabled={!consent || launching}
          >
            {launching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowRight className="h-4 w-4" />
            )}
            Launch verification
          </Button>
        </CardContent>
      </Card>

      <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <ShieldCheck className="mb-4 h-6 w-6 text-blue-600" />
          <CardTitle>Verification status</CardTitle>
          <CardDescription className="leading-7">
            Current onboarding status:{" "}
            {state?.administratorIdentityVerificationStatus || "pending"}.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
