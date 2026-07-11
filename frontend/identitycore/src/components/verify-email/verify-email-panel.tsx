"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Loader2,
  MailCheck,
  RefreshCcw,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import {
  resendOrganizationOnboardingEmailVerification,
  verifyOrganizationOnboardingEmail,
} from "@/lib/public-graphql";

type VerifyState = "idle" | "verifying" | "verified" | "error";

export function VerifyEmailPanel({
  token,
  emailFromUrl = "",
}: {
  token?: string;
  emailFromUrl?: string;
}) {
  const [email, setEmail] = useState(emailFromUrl);
  const [state, setState] = useState<VerifyState>(token ? "verifying" : "idle");
  const [message, setMessage] = useState(
    token
      ? "We are verifying your email address now."
      : "Open the verification link from your inbox to continue onboarding.",
  );
  const [resending, setResending] = useState(false);
  const [resendFeedback, setResendFeedback] = useState<{
    kind: "error" | "success";
    title: string;
    message: string;
  } | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    verifyOrganizationOnboardingEmail(token)
      .then((payload) => {
        setState("verified");
        setMessage(payload.message);
      })
      .catch((error) => {
        setState("error");
        setMessage(getErrorMessage(error));
      });
  }, [token]);

  async function handleResend() {
    setResending(true);
    setResendFeedback(null);

    try {
      const payload =
        await resendOrganizationOnboardingEmailVerification(email);
      setResendFeedback({
        kind: payload.ok ? "success" : "error",
        title: payload.ok ? "Verification email sent" : "Unable to resend",
        message: payload.message,
      });
    } catch (error) {
      setResendFeedback({
        kind: "error",
        title: "Unable to resend verification email",
        message: getErrorMessage(error),
      });
    } finally {
      setResending(false);
    }
  }

  return (
    <AuthShell
      badge="Email verification"
      title="Verify your business email to continue."
      description="IdentityCore requires email verification before a workspace administrator can continue organization onboarding."
    >
      <Card className="mx-auto w-full max-w-md rounded-4xl border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <MailCheck className="h-5 w-5" aria-hidden="true" />
          </div>

          <CardTitle>
            {state === "verified"
              ? "Email verified"
              : state === "error"
                ? "We couldn't verify this link"
                : "Check your inbox"}
          </CardTitle>
          <CardDescription className="leading-7">{message}</CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex gap-3">
              {state === "verifying" ? (
                <Loader2
                  className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-blue-600"
                  aria-hidden="true"
                />
              ) : state === "verified" ? (
                <CheckCircle2
                  className="mt-0.5 h-5 w-5 shrink-0 text-blue-600"
                  aria-hidden="true"
                />
              ) : (
                <RefreshCcw
                  className="mt-0.5 h-5 w-5 shrink-0 text-amber-600"
                  aria-hidden="true"
                />
              )}
              <div>
                <p className="text-sm font-medium">What happens next?</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  After verification, you can sign in, submit organization
                  details, complete administrator identity verification, and
                  wait for platform review.
                </p>
              </div>
            </div>
          </div>

          <Button asChild size="lg" className="w-full rounded-xl">
            <Link href="/login">
              Continue to sign in
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </Button>

          <div className="space-y-3">
            {resendFeedback ? (
              <InlineStatus
                kind={resendFeedback.kind}
                title={resendFeedback.title}
                message={resendFeedback.message}
              />
            ) : null}

            <Input
              type="email"
              placeholder="Business email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="w-full rounded-xl"
              disabled={resending || !email}
              onClick={handleResend}
            >
              {resending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              )}
              Resend verification email
            </Button>
          </div>

          <p className="text-center text-sm text-muted-foreground">
            Used the wrong email?{" "}
            <Link href="/register" className="font-medium text-blue-600">
              Create a new workspace
            </Link>
          </p>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
