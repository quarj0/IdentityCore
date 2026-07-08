import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Code2,
  KeyRound,
  TerminalSquare,
  Webhook,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { FeatureCard } from "@/components/marketing/feature-card";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

const developerFeatures = [
  {
    title: "REST APIs",
    description:
      "Create identity workflows, verification sessions, hosted links, and retrieve trusted outcomes.",
    icon: Code2,
  },
  {
    title: "Webhooks",
    description:
      "Receive workflow events when verifications complete, require review, fail, expire, or change state.",
    icon: Webhook,
  },
  {
    title: "API keys",
    description:
      "Manage sandbox and production credentials for each workspace and environment.",
    icon: KeyRound,
  },
  {
    title: "Sandbox",
    description:
      "Test workflows safely with sandbox verification responses before requesting production access.",
    icon: TerminalSquare,
  },
];

export default function DevelopersPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/developers" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[600px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:gap-16 lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Developers
              </Badge>

              <h1 className="mt-6 max-w-5xl text-4xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                APIs for building identity workflows into your product.
              </h1>

              <p className="mt-7 max-w-2xl text-base leading-8 text-muted-foreground sm:text-lg">
                IdentityCore gives developers the APIs, webhooks, sandbox,
                events, and documentation needed to build identity workflows
                without rebuilding identity infrastructure.
              </p>

              <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <Button
                  asChild
                  size="lg"
                  className="w-full justify-between rounded-xl sm:w-auto sm:justify-center"
                >
                  <a href={DOCS_URL}>
                    Open documentation
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="w-full justify-between rounded-xl sm:w-auto sm:justify-center"
                >
                  <Link href="/platform">
                    <BookOpen className="h-4 w-4" />
                    Explore platform
                  </Link>
                </Button>
              </div>
            </div>

            <Card className="overflow-hidden rounded-[2rem] border-slate-200/80 bg-slate-950 text-white shadow-[0_24px_80px_rgba(15,23,42,0.16)]">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="text-base">
                  Create workflow session
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Simple API surface, infrastructure behind it.
                </CardDescription>
              </CardHeader>

              <pre className="overflow-x-auto whitespace-pre-wrap break-words p-5 text-xs leading-7 text-slate-200 sm:p-6 sm:text-sm sm:whitespace-pre">
                {`POST /api/v1/workflow-sessions

{
  "workflow": "customer-onboarding",
  "subject": {
    "email": "person@example.com"
  },
  "return_url": "https://app.example.com/complete"
}

→ verification_url
→ webhook result
→ audit record`}
              </pre>
            </Card>
          </div>
        </section>

        <Section>
          <SectionHeader
            eyebrow="Developer platform"
            title="Everything needed to integrate identity infrastructure."
          />

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {developerFeatures.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </Section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Documentation portal
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                The full API reference belongs in the developer portal.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                This page introduces developer capabilities. The dedicated
                developer portal contains guides, API references, examples,
                changelog, SDK documentation, and future API explorers.
              </p>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
              <div className="grid gap-3">
                {[
                  "Quickstart guides",
                  "REST API reference",
                  "Webhook event reference",
                  "Authentication and API keys",
                  "Sandbox testing",
                  "SDK examples",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm font-medium text-slate-100"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <MarketingCTA
          title="Build identity workflows with developer-friendly infrastructure."
          description="Start in sandbox, test workflows, connect webhooks, and move toward production when your organization is approved."
          secondaryHref="/templates"
          secondaryLabel="Browse templates"
        />
      </main>

      <MarketingFooter />
    </div>
  );
}
