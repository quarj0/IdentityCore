import Link from "next/link";
import {
  ArrowRight,
  Boxes,
  BrainCircuit,
  Check,
  Cloud,
  Code2,
  Database,
  GitBranch,
  KeyRound,
  Layers3,
  LockKeyhole,
  Network,
  Shield,
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
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

const infrastructureLayers = [
  {
    title: "Workflow Engine",
    description:
      "Design identity workflows that combine verification, policies, providers, and human review.",
    icon: Workflow,
  },
  {
    title: "Provider Orchestration",
    description:
      "Use IdentityCore services, connect third-party providers, or bring your own internal systems.",
    icon: Network,
  },
  {
    title: "Policy Engine",
    description:
      "Apply rules by organization, country, risk level, use case, or deployment environment.",
    icon: GitBranch,
  },
  {
    title: "Developer Platform",
    description:
      "Build with REST APIs, webhooks, SDKs, sandbox projects, and dashboard-managed credentials.",
    icon: Code2,
  },
  {
    title: "Data Control",
    description:
      "Keep identity data private with signed access, retention controls, and deployment flexibility.",
    icon: Database,
  },
  {
    title: "Trust Services",
    description:
      "Add verification, biometrics, audit, consent, risk scoring, and future identity credentials.",
    icon: Shield,
  },
];

const providerRows = [
  ["OCR", "IdentityCore OCR", "PaddleOCR", "Google Vision", "Government OCR"],
  ["Face", "IdentityCore Face", "InsightFace", "Custom Model", "National DB"],
  [
    "Liveness",
    "IdentityCore Liveness",
    "Active Challenge",
    "Vendor API",
    "Internal AI",
  ],
  ["Risk", "IdentityCore Risk", "Rules Engine", "Watchlists", "Custom Signals"],
];

const identityServices = [
  "Identity verification",
  "Document intelligence",
  "Biometric matching",
  "Liveness detection",
  "Consent records",
  "Audit trails",
  "Risk scoring",
  "Policy decisions",
];

const deploymentOptions = [
  {
    title: "Cloud",
    description:
      "Run IdentityCore as a managed SaaS platform for fast adoption.",
  },
  {
    title: "Private Cloud",
    description:
      "Deploy into controlled infrastructure for enterprise workloads.",
  },
  {
    title: "On-Premise",
    description:
      "Support sensitive environments that require local infrastructure.",
  },
  {
    title: "Hybrid",
    description:
      "Combine your existing identity systems with IdentityCore workflows.",
  },
];

const builderSteps = [
  "Choose workflow",
  "Connect providers",
  "Configure policies",
  "Publish to API or hosted link",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[760px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),radial-gradient(circle_at_top_right,rgba(79,70,229,0.12),transparent_30%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[1fr_0.95fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Digital identity infrastructure
              </Badge>

              <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Build your identity stack on IdentityCore.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                Use our verification services, bring your own providers, or
                combine both through one secure infrastructure layer for
                identity workflows, policies, APIs, and trust operations.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg" className="rounded-xl">
                  <Link href="/register">
                    Start building
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-xl"
                >
                  <a href={DOCS_URL}>
                    <Code2 className="h-4 w-4" />
                    Read documentation
                  </a>
                </Button>
              </div>

              <div className="mt-10 grid gap-3 text-sm text-muted-foreground sm:grid-cols-3">
                {[
                  "Bring your own providers",
                  "Own your identity data",
                  "Deploy anywhere later",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-blue-600" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <IdentityStackPreview />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
              <div>
                <p className="text-sm font-medium text-blue-600">
                  Infrastructure layer
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                  Everything needed to build trusted identity systems.
                </h2>
              </div>

              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore gives organizations the core infrastructure for
                identity workflows: providers, policies, verification services,
                data controls, auditability, and developer integration.
              </p>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {infrastructureLayers.map((item) => {
                const Icon = item.icon;

                return (
                  <Card
                    key={item.title}
                    className="group rounded-3xl border-slate-200 bg-white p-2 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl"
                  >
                    <CardHeader className="p-6">
                      <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 ring-1 ring-slate-200 group-hover:bg-blue-50 group-hover:text-blue-700">
                        <Icon className="h-5 w-5" strokeWidth={1.75} />
                      </div>

                      <CardTitle>{item.title}</CardTitle>
                      <CardDescription className="pt-2 leading-7">
                        {item.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Bring your own providers
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Use IdentityCore services, your own systems, or both.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                IdentityCore does not lock you into one OCR, biometric, risk, or
                government provider. Connect the providers your organization
                already trusts and orchestrate them through one workflow engine.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                {["OCR", "Face", "Liveness", "Risk", "Government APIs"].map(
                  (item) => (
                    <span
                      key={item}
                      className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200"
                    >
                      {item}
                    </span>
                  ),
                )}
              </div>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-5 shadow-2xl">
              <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm font-medium text-white">
                    Provider routing
                  </p>
                  <Badge className="rounded-full text-xs bg-blue-600 px-2 py-1">
                    Configurable
                  </Badge>
                </div>

                <div className="space-y-3">
                  {providerRows.map(([category, ...providers]) => (
                    <div
                      key={category}
                      className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                    >
                      <p className="text-xs font-medium uppercase tracking-wide text-blue-300">
                        {category}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {providers.map((provider) => (
                          <span
                            key={provider}
                            className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-200"
                          >
                            {provider}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-600">
                Workflow operating system
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Build identity workflows without rebuilding identity logic.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                Create workflows for onboarding, verification, access,
                credential checks, and trust operations. Start with templates or
                build your own from reusable identity services.
              </p>
            </div>

            <Card className="rounded-[2rem] border-slate-200 bg-white p-2 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
              <CardContent className="p-6">
                <div className="grid gap-4">
                  {builderSteps.map((step, index) => (
                    <div key={step} className="flex items-center gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-sm font-semibold text-blue-700 ring-1 ring-blue-100">
                        {index + 1}
                      </div>
                      <div className="flex-1 rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                        <p className="text-sm font-medium">{step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="bg-slate-50 py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                Identity services
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Verification is one service. The platform is the foundation.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                IdentityCore starts with verification and expands into the
                reusable trust services organizations need to run modern digital
                identity operations.
              </p>
            </div>

            <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {identityServices.map((service) => (
                <div
                  key={service}
                  className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                    <Layers3 className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium">{service}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-7xl gap-6 px-6 lg:grid-cols-4">
            {deploymentOptions.map((option) => (
              <Card key={option.title} className="rounded-3xl p-2 shadow-sm">
                <CardHeader>
                  <Cloud className="mb-4 h-6 w-6 text-blue-600" />
                  <CardTitle>{option.title}</CardTitle>
                  <CardDescription className="leading-7">
                    {option.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Security and governance
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Built for organizations that handle sensitive identity data.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                IdentityCore is designed around privacy, tenant isolation,
                consent, auditability, signed media access, and
                policy-controlled decisioning.
              </p>
            </div>

            <div className="grid gap-3">
              {[
                "Tenant isolation across every workflow",
                "Private media storage with signed access",
                "Consent and retention controls",
                "Policy-driven decisions with audit trails",
              ].map((point) => (
                <div
                  key={point}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <LockKeyhole className="h-5 w-5 text-blue-300" />
                  <span className="text-sm font-medium text-slate-100">
                    {point}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <h2 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Build your identity platform without starting from zero.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
              Use IdentityCore as the infrastructure layer for verification,
              onboarding, provider orchestration, identity workflows, and future
              trust services.
            </p>

            <div className="mt-10 flex justify-center gap-3">
              <Button asChild size="lg" className="rounded-xl">
                <Link href="/register">
                  Create workspace
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                size="lg"
                className="rounded-xl"
              >
                <Link href="/security">Explore security</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
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

function IdentityStackPreview() {
  return (
    <div className="relative">
      <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-blue-600/10 blur-3xl" />

      <Card className="overflow-hidden rounded-[2rem] border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader className="border-b bg-slate-50/70">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">IdentityCore stack</CardTitle>
              <CardDescription>
                Orchestrate services, providers, and policies
              </CardDescription>
            </div>
            <Badge className="rounded-full bg-blue-600 px-2 py-1 text-xs text-white">
              Infrastructure
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <div className="rounded-3xl border border-slate-200 bg-slate-950 p-5 text-white">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center">
              <p className="text-sm font-medium">Workflow Engine</p>
              <p className="mt-1 text-xs text-slate-300">
                Policies · Events · Review · Automation
              </p>
            </div>

            <div className="my-5 grid gap-3 sm:grid-cols-3">
              {[
                ["Providers", Network],
                ["Identity APIs", KeyRound],
                ["Trust Services", BrainCircuit],
              ].map(([label, Icon]) => {
                const LucideIcon = Icon as typeof Network;

                return (
                  <div
                    key={label as string}
                    className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 text-center"
                  >
                    <LucideIcon className="mx-auto mb-3 h-5 w-5 text-blue-300" />
                    <p className="text-xs font-medium">{label as string}</p>
                  </div>
                );
              })}
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-blue-300">
                Connected systems
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  "Customer apps",
                  "Government APIs",
                  "Internal AI",
                  "Object storage",
                  "Webhooks",
                ].map((item) => (
                  <span
                    key={item}
                    className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-200"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            {[
              ["Data", Database],
              ["Security", Shield],
              ["Services", Boxes],
            ].map(([label, Icon]) => {
              const LucideIcon = Icon as typeof Database;

              return (
                <div
                  key={label as string}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center"
                >
                  <LucideIcon className="mx-auto mb-2 h-4 w-4 text-blue-600" />
                  <p className="text-xs font-medium">{label as string}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
