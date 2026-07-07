import Link from "next/link";
import { ArrowRight, Mail } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

export function LoginPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 -z-10 h-[620px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

        <section className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-28">
          <div>
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Sign in
            </Badge>

            <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:leading-[0.98]">
              Continue managing your identity infrastructure.
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
              Access your workspace, configure workflows, manage providers,
              review activity, and prepare your organization for production
              access.
            </p>
          </div>

          <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
            <CardHeader>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <Mail className="h-5 w-5" />
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
                    placeholder="you@company.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" />
                </div>

                <Button type="button" size="lg" className="w-full rounded-xl">
                  Sign in
                  <ArrowRight className="h-4 w-4" />
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
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
