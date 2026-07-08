"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, LockKeyhole } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  toast,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { getErrorMessage } from "@/lib/api-client";
import { resetPassword } from "@/lib/public-graphql";

export function ResetPasswordForm({ token = "" }: { token?: string }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirmPassword) {
      toast({
        title: "Passwords do not match",
        description: "Enter the same new password in both fields.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const payload = await resetPassword(token, password);
      toast({
        title: "Password reset complete",
        description: payload.message,
      });
      router.push("/login");
    } catch (error) {
      toast({
        title: "Unable to reset password",
        description: getErrorMessage(error),
        variant: "destructive",
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
      <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
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
              <div className="space-y-2">
                <Label htmlFor="password">New password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm new password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
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
            </form>
          ) : (
            <div className="space-y-4 text-sm text-muted-foreground">
              <p>A valid reset token is required to change your password.</p>
              <Link href="/forgot-password" className="font-medium text-blue-600">
                Request a new reset link
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </AuthShell>
  );
}
