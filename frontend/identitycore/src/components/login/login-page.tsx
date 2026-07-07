import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";
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

export function LoginPageContent() {
  return (
    <AuthShell
      badge="Sign in"
      title="Continue managing your identity infrastructure."
      description="Access your workspace, configure workflows, manage providers, review activity, and prepare your organization for production access."
    >
      <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
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
          <form className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Business email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
              />
            </div>

            <Button type="button" size="lg" className="w-full rounded-xl">
              Sign in
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              New to IdentityCore?{" "}
              <Link href="/register" className="font-medium text-blue-600">
                Create workspace
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
