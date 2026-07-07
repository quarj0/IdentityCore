import Link from "next/link";
import { ArrowRight, CheckCircle2, MailCheck, RefreshCcw } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";

export default function VerifyEmailPage() {
  return (
    <AuthShell
      badge="Email verification"
      title="Verify your business email to continue."
      description="IdentityCore requires email verification before a workspace administrator can continue organization onboarding."
    >
      <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <MailCheck className="h-5 w-5" aria-hidden="true" />
          </div>

          <CardTitle>Check your inbox</CardTitle>
          <CardDescription className="leading-7">
            We sent a verification link to your business email. Open the link to
            activate your account and continue setting up your organization.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex gap-3">
              <CheckCircle2
                className="mt-0.5 h-5 w-5 shrink-0 text-blue-600"
                aria-hidden="true"
              />
              <div>
                <p className="text-sm font-medium">What happens next?</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  After verification, you can sign in, complete organization
                  details, verify the administrator identity, and submit for
                  production approval.
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

          <Button
            type="button"
            variant="outline"
            size="lg"
            className="w-full rounded-xl"
          >
            <RefreshCcw className="h-4 w-4" aria-hidden="true" />
            Resend verification email
          </Button>

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
