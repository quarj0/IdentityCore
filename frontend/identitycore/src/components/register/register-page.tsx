import Link from "next/link";
import { ArrowRight, Building2, ShieldCheck } from "lucide-react";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const onboardingSteps = [
  "Create workspace",
  "Verify email",
  "Complete organization profile",
  "Verify administrator identity",
  "Submit for production approval",
];

const tiers = [
  ["Tier 0", "Trial", "Sandbox only"],
  ["Tier 1", "Verified", "Production access after approval"],
  ["Tier 2", "Trusted", "Higher limits and advanced workflows"],
  ["Tier 3", "Enterprise", "Dedicated deployment and custom support"],
];

export function RegisterPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 -z-10 h-[760px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

        <section className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-[0.9fr_1.1fr] lg:items-start lg:py-28">
          <div>
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Create workspace
            </Badge>

            <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:leading-[0.98]">
              Start building your identity infrastructure.
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
              Register yourself and your organization together. IdentityCore
              gives every organization a workspace, sandbox access, and a path
              toward production approval.
            </p>

            <div className="mt-10 space-y-4">
              {onboardingSteps.map((step, index) => (
                <div key={step} className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-blue-700 ring-1 ring-blue-100">
                    {index + 1}
                  </div>
                  <span className="text-sm font-medium">{step}</span>
                </div>
              ))}
            </div>

            <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-blue-600" />
                <p className="font-medium">Organization tiers</p>
              </div>

              <div className="mt-5 grid gap-3">
                {tiers.map(([level, name, description]) => (
                  <div
                    key={level}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-sm font-semibold">
                      {level} — {name}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <Card className="rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
            <CardHeader>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <Building2 className="h-5 w-5" />
              </div>
              <CardTitle>Create your organization workspace</CardTitle>
              <CardDescription>
                This will later call the registerOrganizationOnboarding GraphQL
                mutation.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form className="space-y-8">
                <div>
                  <p className="text-sm font-semibold">Administrator</p>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full name</Label>
                      <Input id="fullName" placeholder="Angela Doe" />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="email">Business email</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="you@company.com"
                      />
                    </div>

                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="password">Password</Label>
                      <Input id="password" type="password" />
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold">Organization</p>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="organizationName">
                        Organization name
                      </Label>
                      <Input
                        id="organizationName"
                        placeholder="Acme Financial Services"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Organization type</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="government">Government</SelectItem>
                          <SelectItem value="financial_institution">
                            Financial institution
                          </SelectItem>
                          <SelectItem value="education">Education</SelectItem>
                          <SelectItem value="healthcare">Healthcare</SelectItem>
                          <SelectItem value="enterprise">Enterprise</SelectItem>
                          <SelectItem value="ngo">NGO</SelectItem>
                          <SelectItem value="startup">Startup</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="country">Country</Label>
                      <Input id="country" placeholder="Ghana" />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="website">Website</Label>
                      <Input id="website" placeholder="https://company.com" />
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
                      <Input id="phone" placeholder="+233..." />
                    </div>
                  </div>
                </div>

                <Button type="button" size="lg" className="w-full rounded-xl">
                  Create workspace
                  <ArrowRight className="h-4 w-4" />
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
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
