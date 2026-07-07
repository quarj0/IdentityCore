import Link from "next/link";
import {
  ArrowRight,
  Cloud,
  Code2,
  Database,
  GitBranch,
  Layers3,
  LockKeyhole,
  Network,
  Workflow,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { PlatformDiagram } from "@/components/marketing/platform-diagram";
import { ArchitectureLayerList } from "@/components/platform/architecture-layer-list";
import { PlatformComponentCard } from "@/components/platform/platform-component-card";
import { ProviderGrid } from "@/components/platform/provider-grid";
import { ServiceGrid } from "@/components/platform/service-grid";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

const components = [
  {
    title: "Workflow Engine",
    description:
      "Build identity workflows for onboarding, verification, access, review, and trust operations.",
    icon: Workflow,
  },
  {
    title: "Provider Router",
    description:
      "Route identity tasks to IdentityCore services, third-party vendors, government APIs, or internal systems.",
    icon: Network,
  },
  {
    title: "Policy Engine",
    description:
      "Apply business rules, thresholds, review logic, and country-specific requirements without hardcoding.",
    icon: GitBranch,
  },
  {
    title: "Identity Services",
    description:
      "Use verification, document intelligence, biometrics, consent, audit, risk, and future credential services.",
    icon: Layers3,
  },
  {
    title: "Developer Platform",
    description:
      "Integrate through REST APIs, webhooks, sandbox projects, API keys, SDKs, and documentation.",
    icon: Code2,
  },
  {
    title: "Data Control",
    description:
      "Keep sensitive media, evidence, audit records, and identity data under controlled access and retention.",
    icon: Database,
  },
];

const deployments = [
  {
    title: "Managed cloud",
    description:
      "Use IdentityCore as a hosted platform for fast onboarding and lower operational overhead.",
  },
  {
    title: "Private cloud",
    description:
      "Deploy into controlled infrastructure for enterprise and regulated environments.",
  },
  {
    title: "On-premise",
    description:
      "Run IdentityCore inside customer-controlled infrastructure where data residency matters.",
  },
  {
    title: "Hybrid",
    description:
      "Combine IdentityCore cloud workflows with internal providers, databases, and government systems.",
  },
];

const governanceItems = [
  "Tenant isolation",
  "Consent records",
  "Signed media access",
  "Audit logs",
  "Policy versioning",
  "Role-based access",
];

export function PlatformPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/platform" />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[620px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Platform
              </Badge>

              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                The infrastructure layer for digital identity.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore gives organizations the building blocks to create,
                control, and scale identity systems using workflows, providers,
                policies, APIs, and secure data infrastructure.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
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
                  <a href={DOCS_URL}>
                    <Code2 className="h-4 w-4" />
                    View docs
                  </a>
                </Button>
              </div>
            </div>

            <PlatformDiagram />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                Core components
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                IdentityCore is built as a platform, not a single verification
                product.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                Verification is only one capability. The platform provides the
                infrastructure needed to orchestrate trust across many identity
                workflows.
              </p>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {components.map((item) => (
                <PlatformComponentCard key={item.title} {...item} />
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Bring your own stack
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Use our services, connect yours, or combine both.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                IdentityCore is designed to sit above identity providers. Your
                organization can use built-in services or route workflows to
                trusted external systems.
              </p>
            </div>

            <ProviderGrid />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div>
              <p className="text-sm font-medium text-blue-600">Architecture</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                A layered identity platform for modern organizations.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                Each layer has a clear responsibility, making the platform
                easier to extend, secure, integrate, and deploy.
              </p>
            </div>

            <ArchitectureLayerList />
          </div>
        </section>

        <section className="bg-slate-50 py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                Identity services
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Reusable trust services for many identity workflows.
              </h2>
            </div>

            <ServiceGrid />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
              <div>
                <p className="text-sm font-medium text-blue-600">Deployment</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                  Deploy identity infrastructure where your organization needs
                  it.
                </h2>
              </div>

              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore is designed to support hosted SaaS first, while
                keeping the architecture ready for private, hybrid, and
                on-premise deployments.
              </p>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {deployments.map((item) => (
                <Card key={item.title} className="rounded-3xl p-2 shadow-sm">
                  <CardHeader>
                    <Cloud className="mb-4 h-6 w-6 text-blue-600" />
                    <CardTitle>{item.title}</CardTitle>
                    <CardDescription className="leading-7">
                      {item.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">Governance</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Built for trust, privacy, and operational control.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                Identity systems require more than APIs. They need governance:
                audit trails, consent, permissions, retention, tenant isolation,
                and explainable decisions.
              </p>
            </div>

            <div className="grid gap-3">
              {governanceItems.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <LockKeyhole className="h-5 w-5 text-blue-300" />
                  <span className="text-sm font-medium text-slate-100">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <h2 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Build identity systems without rebuilding identity infrastructure.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
              Start with IdentityCore as your workflow, provider, policy, and
              trust infrastructure layer.
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
                <Link href="/how-it-works">See how it works</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
