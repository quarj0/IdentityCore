"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
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
  MfaSignIn,
  type MfaTransaction,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordInput } from "@/components/auth/password-input";
import { InlineStatus } from "@/components/feedback/inline-status";
import { saveAuthSession } from "@/lib/auth";
import { getErrorMessage, restRequest } from "@/lib/api-client";
import { login, type LoginResponse } from "@/lib/onboarding-api";

const dashboardUrl =
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export function LoginForm() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [transaction, setTransaction] = useState<MfaTransaction | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = await login(email, password);
      setPassword("");
      if ("mfa_required" in payload) setTransaction(payload);
      else complete(payload);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  function complete(payload: LoginResponse) {
    setTransaction(null);
    saveAuthSession({ accessToken: payload.tokens.access, user: payload.user });
    window.location.assign(dashboardUrl);
  }

  return (
    <AuthShell
      badge="Sign in"
      title="Continue managing your identity infrastructure."
      description="Access your workspace, configure workflows, manage providers, review activity, and prepare your organization for production access."
    >
      <Card className="mx-auto w-full max-w-md rounded-4xl border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <Mail className="h-5 w-5" aria-hidden="true" />
          </div>
          <CardTitle>Sign in to IdentityCore</CardTitle>
          <CardDescription>
            Use your business email to access your organization workspace.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {transaction ? (
            <MfaSignIn<LoginResponse>
              transaction={transaction}
              request={(path, body) =>
                restRequest(
                  path,
                  { method: "POST", body: JSON.stringify(body) },
                  { useAuth: false },
                )
              }
              onComplete={complete}
              onCancel={() => setTransaction(null)}
            />
          ) : (
            <form className="space-y-5" onSubmit={handleSubmit}>
              {searchParams.get("reason") === "session_expired" ? (
                <InlineStatus
                  kind="error"
                  title="Session expired"
                  message="Sign in again to continue where you left off."
                />
              ) : null}
              {errorMessage ? (
                <InlineStatus
                  kind="error"
                  title="Unable to sign in"
                  message={errorMessage}
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

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <PasswordInput
                  id="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>

              <p className="text-right text-sm">
                <Link
                  href="/forgot-password"
                  className="font-medium text-blue-600"
                >
                  Forgot password?
                </Link>
              </p>

              <Button
                type="submit"
                size="lg"
                className="w-full rounded-xl"
                disabled={submitting}
              >
                {submitting ? (
                  <Loader2
                    className="h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                ) : (
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                )}
                Sign in
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                New to IdentityCore?{" "}
                <Link href="/register" className="font-medium text-blue-600">
                  Create workspace
                </Link>
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </AuthShell>
  );
}
