import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  Check,
  Code2,
  Fingerprint,
  Globe2,
  LockKeyhole,
  ScanFace,
  Shield,
  Sparkles,
  Workflow,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Separator,
} from "@identitycore/ui";

const featureCards = [
  {
    title: "Global document intelligence",
    description:
      "Parse passports, residence permits, licenses, and national IDs with confidence scoring and normalized outputs.",
    icon: Globe2,
  },
  {
    title: "Face match and liveness",
    description:
      "Combine selfie capture, spoof detection, and biometric verification in one guided session.",
    icon: ScanFace,
  },
  {
    title: "Policy-first orchestration",
    description:
      "Design reusable verification flows that adapt by market, risk profile, or business line without rewriting client code.",
    icon: Workflow,
  },
];

const stats = [
  { label: "Verification completion", value: "92.4%" },
  { label: "Median decision time", value: "< 45 sec" },
  { label: "Supported markets", value: "190+" },
];

const trustPoints = [
  "Built for onboarding, marketplace trust, and regulated account recovery.",
  "Secure audit trails, reviewer workflows, and webhook-driven handoffs.",
  "Developer docs and dashboard tools designed for fast internal adoption.",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b border-border/70 bg-background/72 backdrop-blur-xl">
        <div className="mx-auto flex h-18 w-full max-w-7xl items-center px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-[0_18px_40px_-22px_hsl(var(--primary)/0.9)]">
              <Fingerprint className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-[0.18em] text-foreground">
                IDENTITYCORE
              </div>
              <div className="text-xs text-muted-foreground">
                Verification infrastructure
              </div>
            </div>
          </Link>

          <nav className="ml-auto hidden items-center gap-6 md:flex">
            <Link href="/pricing" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Pricing
            </Link>
            <Link href="/security" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Security
            </Link>
            <Link href="/company" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Company
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <a href="http://localhost:3003" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Docs
            </a>
            <Button asChild variant="outline" size="sm">
              <a href="http://localhost:3000">Dashboard</a>
            </Button>
          </nav>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden px-6 pb-20 pt-16 lg:px-8 lg:pb-28 lg:pt-24">
          <div className="absolute inset-x-0 top-0 -z-10 h-[32rem] bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.18),transparent_28%),radial-gradient(circle_at_top_right,rgba(37,99,235,0.14),transparent_24%)]" />
          <div className="mx-auto grid w-full max-w-7xl gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-center">
            <div className="space-y-8">
              <Badge variant="info" className="px-4 py-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Built for modern trust and compliance teams
              </Badge>

              <div className="space-y-5">
                <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
                  Verification flows your product team can actually ship.
                </h1>
                <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                  IdentityCore gives engineering, compliance, and operations one shared system for identity checks, manual review, and policy control.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button asChild size="lg" className="gap-2">
                  <a href="http://localhost:3000">
                    Open dashboard
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>
                <Button asChild size="lg" variant="outline" className="gap-2">
                  <a href="http://localhost:3003">
                    <Code2 className="h-4 w-4" />
                    Explore docs
                  </a>
                </Button>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                {stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-2xl border border-border/70 bg-background/72 px-4 py-4 shadow-[0_20px_48px_-40px_rgba(15,23,42,0.45)] backdrop-blur-sm"
                  >
                    <div className="text-2xl font-semibold tracking-tight text-foreground">
                      {stat.value}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:pl-8">
              <Card className="overflow-hidden">
                <CardHeader className="border-b border-border/70 bg-linear-to-br from-primary/[0.08] via-background to-accent/[0.18]">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <CardTitle className="text-xl">Verification stack</CardTitle>
                      <CardDescription>
                        One operating layer across capture, review, and risk decisions.
                      </CardDescription>
                    </div>
                    <Badge variant="outline">Live system view</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 p-6">
                  {featureCards.map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <div
                        key={feature.title}
                        className="rounded-2xl border border-border/60 bg-background/80 p-4"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                            <Icon className="h-5 w-5" />
                          </div>
                          <div className="space-y-1.5">
                            <div className="text-base font-semibold text-foreground">
                              {feature.title}
                            </div>
                            <p className="text-sm leading-6 text-muted-foreground">
                              {feature.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="px-6 py-20 lg:px-8">
          <div className="mx-auto grid w-full max-w-7xl gap-10 lg:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
            <div className="space-y-4">
              <Badge variant="secondary">Why teams choose us</Badge>
              <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Serious verification product, not a stitched-together set of endpoints.
              </h2>
              <p className="max-w-xl text-base leading-7 text-muted-foreground">
                The strongest products here are the ones that feel aligned across compliance expectations, engineering ergonomics, and customer trust. That’s the standard we’re aiming for.
              </p>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <Card className="md:col-span-2">
                <CardContent className="grid gap-4 p-6 md:grid-cols-3">
                  {trustPoints.map((point) => (
                    <div key={point} className="flex gap-3">
                      <div className="mt-0.5 text-primary">
                        <Check className="h-4 w-4" />
                      </div>
                      <p className="text-sm leading-6 text-muted-foreground">
                        {point}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <Shield className="h-5 w-5 text-primary" />
                  <CardTitle>Designed for regulated trust</CardTitle>
                  <CardDescription>
                    Strong operator surfaces, review states, and structured auditability.
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader>
                  <LockKeyhole className="h-5 w-5 text-primary" />
                  <CardTitle>Security is native</CardTitle>
                  <CardDescription>
                    Encryption, access control boundaries, and evidentiary workflows are part of the product shape.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
