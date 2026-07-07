import Link from "next/link";
import {
  ArrowRight,
  Database,
  FileLock2,
  Fingerprint,
  GitBranch,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const securityPillars = [
  {
    title: "Tenant isolation",
    description:
      "Every organization operates within strict tenant boundaries across APIs, workflows, storage, and audit records.",
    icon: ShieldCheck,
  },
  {
    title: "Private media access",
    description:
      "Identity documents, selfies, liveness videos, and reports stay private and are accessed only through signed URLs.",
    icon: FileLock2,
  },
  {
    title: "Policy governance",
    description:
      "Verification outcomes are controlled by versioned policies, not opaque AI decisions.",
    icon: GitBranch,
  },
  {
    title: "Auditability",
    description:
      "Sensitive actions are recorded so organizations can understand who did what, when, and why.",
    icon: Database,
  },
];

const privateDefaults = [
  ["Media", "Private buckets and signed access"],
  ["Decisions", "Policy-controlled and explainable"],
  ["Tenants", "Organization-scoped access boundaries"],
  ["Events", "Audit logs and webhook traceability"],
] as const;

const controls = [
  "Encryption in transit and at rest",
  "Role-based access control",
  "Signed upload and download URLs",
  "Consent-aware verification workflows",
  "Policy versioning and review trails",
  "Private object storage by default",
  "API key and webhook secret management",
  "Future private cloud and on-premise support",
];

export function SecurityPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/security" />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[600px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Security
              </Badge>

              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Security and governance for digital identity infrastructure.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore is designed for sensitive identity workflows where
                privacy, auditability, tenant isolation, and data control are
                not optional.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg" className="rounded-xl">
                  <Link href="/platform">
                    Explore platform
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-xl"
                >
                  <Link href="/how-it-works">See how it works</Link>
                </Button>
              </div>
            </div>

            <Card className="rounded-[2rem] border-slate-200/80 bg-white/85 p-2 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
              <CardHeader>
                <LockKeyhole className="mb-4 h-8 w-8 text-blue-600" />
                <CardTitle>Private by default</CardTitle>
                <CardDescription className="leading-7">
                  IdentityCore treats all identity documents, biometric media,
                  evidence, and audit records as sensitive by default.
                </CardDescription>
              </CardHeader>

              <div className="grid gap-3 p-6 pt-0">
                {privateDefaults.map(([title, value]) => (
                  <div
                    key={title}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-sm font-medium">{title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {value}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                Security model
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Built around the realities of identity data.
              </h2>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {securityPillars.map((pillar) => {
                const Icon = pillar.icon;

                return (
                  <Card
                    key={pillar.title}
                    className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm"
                  >
                    <CardHeader>
                      <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                        <Icon className="h-5 w-5" />
                      </div>
                      <CardTitle>{pillar.title}</CardTitle>
                      <CardDescription className="leading-7">
                        {pillar.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Governance controls
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Control access, data, policies, and evidence.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                IdentityCore is designed so organizations can govern how
                identity workflows are created, executed, reviewed, retained,
                and audited.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {controls.map((control) => (
                <div
                  key={control}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <KeyRound className="h-5 w-5 text-blue-300" />
                  <span className="text-sm font-medium text-slate-100">
                    {control}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-600">AI governance</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                AI provides evidence. Policies make decisions.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                IdentityCore separates AI signals from business decisions so
                every outcome can be explained, audited, reviewed, and adjusted
                by policy.
              </p>
            </div>

            <Card className="rounded-[2rem] p-2 shadow-sm">
              <CardHeader>
                <Fingerprint className="mb-4 h-7 w-7 text-blue-600" />
                <CardTitle>Decision transparency</CardTitle>
                <CardDescription className="leading-7">
                  Face match scores, OCR confidence, liveness signals, document
                  quality, provider responses, and policy versions can all be
                  recorded as evidence behind a decision.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        <MarketingCTA
          title="Build identity workflows with security at the foundation."
          description="Use IdentityCore to control providers, policies, data access, evidence, and review across your identity operations."
          secondaryHref="/platform"
          secondaryLabel="Explore platform"
        />
      </main>

      <MarketingFooter />
    </div>
  );
}
