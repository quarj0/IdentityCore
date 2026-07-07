import Link from "next/link";
import { ArrowRight, Building2 } from "lucide-react";
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
import { OrganizationTypePicker } from "@/components/register/organization-type-picker";

export function RegisterPageContent() {
  return (
    <AuthShell
      badge="Create workspace"
      title="Register your organization and start in sandbox."
      description="Create an administrator account and organization workspace together. Production access is unlocked after verification and approval."
    >
      <Card className="w-full rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <Building2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <CardTitle>Create organization workspace</CardTitle>
          <CardDescription>
            You will verify your email before continuing onboarding.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-8">
            <section>
              <p className="text-sm font-semibold">Administrator</p>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    autoComplete="name"
                    placeholder="Kwadwo Owusu Ansah"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Business email</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                  />
                </div>
              </div>
            </section>

            <section>
              <p className="text-sm font-semibold">Organization</p>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="organizationName">Organization name</Label>
                  <Input
                    id="organizationName"
                    placeholder="Acme Financial Services"
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <OrganizationTypePicker />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="country">Country</Label>
                  <Input
                    id="country"
                    autoComplete="country-name"
                    placeholder="Ghana"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="website">Website</Label>
                  <Input
                    id="website"
                    type="url"
                    autoComplete="url"
                    placeholder="https://company.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="supportEmail">Support email</Label>
                  <Input
                    id="supportEmail"
                    type="email"
                    placeholder="support@company.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    placeholder="+233..."
                  />
                </div>
              </div>
            </section>

            <Button type="button" size="lg" className="w-full rounded-xl">
              Create workspace
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Already have a workspace?{" "}
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
