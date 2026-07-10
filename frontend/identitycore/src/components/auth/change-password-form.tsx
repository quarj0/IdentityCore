"use client";

import { useState } from "react";
import { ArrowRight, Loader2, ShieldCheck } from "lucide-react";
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
import { changePassword } from "@/lib/account-graphql";
import { getErrorMessage } from "@/lib/api-client";

export function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
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
    if (newPassword !== confirmPassword) {
      setFeedback({
        kind: "error",
        title: "Passwords do not match",
        message: "Enter the same new password in both fields.",
      });
      return;
    }

    setSubmitting(true);
    try {
      const payload = await changePassword(currentPassword, newPassword);
      setFeedback({
        kind: "success",
        title: "Password changed",
        message: payload.message,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to change password",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Security"
      title="Change your password."
      description="Update your current password for your IdentityCore workspace account."
    >
      <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle>Change password</CardTitle>
          <CardDescription>
            Confirm your current password, then choose a new one.
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
              <Label htmlFor="currentPassword">Current password</Label>
              <PasswordInput
                id="currentPassword"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">New password</Label>
              <PasswordInput
                id="newPassword"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmNewPassword">Confirm new password</Label>
              <PasswordInput
                id="confirmNewPassword"
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
              Change password
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
