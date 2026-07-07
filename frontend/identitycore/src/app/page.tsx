import Link from "next/link";
import {
  ArrowRight,
  Check,
  Code2,
  Globe2,
  LockKeyhole,
  ScanFace,
  Shield,
  Workflow,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const capabilities = [
  {
    title: "Document verification",
    description:
      "Extract and validate data from passports, national IDs, and driver's licenses across 190+ countries.",
    icon: Globe2,
  },
  {
    title: "Biometric checks",
    description:
      "Face matching and liveness detection with configurable confidence thresholds and manual review routing.",
    icon: ScanFace,
  },
  {
    title: "Policy engine",
    description:
      "Define verification requirements by market, risk tier, or use case without changing application code.",
    icon: Workflow,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingHeader />

      <main>
        <section className="border-b border-border">
          <div className="mx-auto max-w-6xl px-6 py-24 lg:py-32">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-muted-foreground">
                Identity verification infrastructure
              </p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-[3.25rem] lg:leading-[1.1]">
                Build compliant identity verification into your product
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore provides document analysis, biometric verification,
                and review workflows through a single API and dashboard — built
                for teams that need reliability at scale.
              </p>
              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg">
                  <a href="http://localhost:3000">
                    Start building
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <a href="http://localhost:3003">
                    <Code2 className="h-4 w-4" />
                    View documentation
                  </a>
                </Button>
              </div>
            </div>

            <dl className="mt-16 grid gap-8 border-t border-border pt-12 sm:grid-cols-3">
              {[
                { value: "92.4%", label: "Completion rate" },
                { value: "< 45s", label: "Median decision time" },
                { value: "190+", label: "Supported countries" },
              ].map((stat) => (
                <div key={stat.label}>
                  <dt className="text-3xl font-semibold tabular-nums tracking-tight">
                    {stat.value}
                  </dt>
                  <dd className="mt-1 text-sm text-muted-foreground">
                    {stat.label}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-6xl px-6">
            <div className="max-w-2xl">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Everything required for production verification
              </h2>
              <p className="mt-4 text-muted-foreground leading-7">
                From document capture to final decision, with audit trails and
                reviewer tools included.
              </p>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-3">
              {capabilities.map((item) => {
                const Icon = item.icon;
                return (
                  <Card key={item.title} className="border-border shadow-none">
                    <CardHeader>
                      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md border border-border bg-muted/50">
                        <Icon
                          className="h-4 w-4 text-foreground"
                          strokeWidth={1.75}
                        />
                      </div>
                      <CardTitle className="text-base">{item.title}</CardTitle>
                      <CardDescription className="leading-6">
                        {item.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        <section className="border-y border-border bg-muted/30 py-24">
          <div className="mx-auto grid max-w-6xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Designed for regulated environments
              </h2>
              <p className="mt-4 text-muted-foreground leading-7">
                Compliance, engineering, and operations teams work from the same
                system — reducing handoffs and improving auditability.
              </p>
            </div>
            <ul className="space-y-4">
              {[
                "Structured audit logs for every verification and review action",
                "Role-based access control for team and reviewer permissions",
                "Webhook-driven integration with your existing systems",
              ].map((point) => (
                <li
                  key={point}
                  className="flex gap-3 text-sm leading-6 text-muted-foreground"
                >
                  <Check
                    className="mt-0.5 h-4 w-4 shrink-0 text-foreground"
                    strokeWidth={2}
                  />
                  {point}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-6xl gap-6 px-6 md:grid-cols-2">
            <Card className="shadow-none">
              <CardHeader>
                <Shield
                  className="mb-2 h-5 w-5 text-muted-foreground"
                  strokeWidth={1.75}
                />
                <CardTitle className="text-base">
                  Compliance-ready workflows
                </CardTitle>
                <CardDescription className="leading-6">
                  Manual review queues, policy versioning, and exportable audit
                  records for regulatory requirements.
                </CardDescription>
              </CardHeader>
            </Card>
            <Card className="shadow-none">
              <CardHeader>
                <LockKeyhole
                  className="mb-2 h-5 w-5 text-muted-foreground"
                  strokeWidth={1.75}
                />
                <CardTitle className="text-base">Enterprise security</CardTitle>
                <CardDescription className="leading-6">
                  Encryption at rest and in transit, least-privilege access, and
                  secure handling of biometric data.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        <section className="border-t border-border py-20">
          <div className="mx-auto max-w-6xl px-6 text-center">
            <h2 className="text-2xl font-semibold tracking-tight">
              Ready to integrate?
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
              Create an account, configure your first policy, and launch a
              verification flow in under an hour.
            </p>
            <div className="mt-8 flex justify-center gap-3">
              <Button asChild size="lg">
                <Link href="/pricing">View pricing</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <a href="http://localhost:3003">Read the docs</a>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <p className="text-sm text-muted-foreground">© 2026 IdentityCore</p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link href="/security" className="hover:text-foreground">
              Security
            </Link>
            <Link href="/company" className="hover:text-foreground">
              Company
            </Link>
            <Link href="/pricing" className="hover:text-foreground">
              Pricing
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
