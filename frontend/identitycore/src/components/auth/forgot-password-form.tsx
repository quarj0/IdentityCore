"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Mail } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import { requestPasswordReset } from "@/lib/public-graphql";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    kind: "error" | "success";
    title: string;
    message: string;
  } | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);
    try {
      const payload = await requestPasswordReset(email);
      setFeedback({
        kind: "success",
        title: "Reset requested",
        message: payload.message,
      });
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to request reset",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Password reset"
      title="Reset your IdentityCore password."
      description="Enter your business email and we will send a password reset link if the account exists."
    >
      <Card className="mx-auto w-full max-w-md rounded-4xl border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <Mail className="h-5 w-5" />
          </div>
          <CardTitle>Forgot password</CardTitle>
          <CardDescription>
            Use your business email to request a secure password reset link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            {feedback ? (
              <InlineStatus
                kind={feedback.kind}
                title={feedback.title}
                message={feedback.message}
              />
            ) : null}

            <div className="space-y-2">
              <Label htmlFor="email">Business email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <Button
              type="submit"
              size="lg"
              className="w-full rounded-xl"
              disabled={submitting}
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
              Send reset link
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Remembered it?{" "}
              <Link href="/login" className="font-medium text-blue-600">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
