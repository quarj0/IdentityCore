"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, LockKeyhole } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Label,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordInput } from "@/components/auth/password-input";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import { resetPassword } from "@/lib/public-graphql";

export function ResetPasswordForm({ token = "" }: { token?: string }) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    kind: "error" | "success";
    title: string;
    message: string;
  } | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    if (password !== confirmPassword) {
      setFeedback({
        kind: "error",
        title: "Passwords do not match",
        message: "Enter the same new password in both fields.",
      });
      return;
    }

    setSubmitting(true);
    try {
      const payload = await resetPassword(token, password);
      setFeedback({
        kind: "success",
        title: "Password reset complete",
        message: payload.message,
      });
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to reset password",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Password reset"
      title="Choose a new password."
      description="Set a new password for your IdentityCore account using the secure reset token."
    >
      <Card className="mx-auto w-full max-w-md rounded-4xl border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <CardTitle>Reset password</CardTitle>
          <CardDescription>
            Enter a strong new password to regain access to your workspace.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {token ? (
            <form className="space-y-5" onSubmit={handleSubmit}>
              {feedback ? (
                <InlineStatus
                  kind={feedback.kind}
                  title={feedback.title}
                  message={feedback.message}
                />
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="password">New password</Label>
                <PasswordInput
                  id="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm new password</Label>
                <PasswordInput
                  id="confirmPassword"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
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
                Reset password
              </Button>
              {feedback?.kind === "success" ? (
                <Button asChild variant="outline" className="w-full rounded-xl">
                  <Link href="/login">Continue to sign in</Link>
                </Button>
              ) : null}
            </form>
          ) : (
            <div className="space-y-4 text-sm text-muted-foreground">
              <p>A valid reset token is required to change your password.</p>
              <Link
                href="/forgot-password"
                className="font-medium text-blue-600"
              >
                Request a new reset link
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </AuthShell>
  );
}
