import Link from "next/link";
import {
  ArrowRight,
  BellRing,
  Code2,
  FileSearch,
  GitBranch,
  Network,
  Workflow,
} from "lucide-react";
import { Badge, Button } from "@identitycore/ui";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { FlowPreview } from "@/components/how-it-works/flow-preview";
import { ProviderRoutingList } from "@/components/how-it-works/provider-routing-list";
import { TeamCardGrid } from "@/components/how-it-works/team-card-grid";
import { UseCaseGrid } from "@/components/how-it-works/use-case-grid";
import { WorkflowStepCard } from "@/components/how-it-works/workflow-step-card";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL ?? "http://localhost:3003";

const steps = [
  {
    title: "Create a workflow",
    description:
      "Start from a template or build a custom identity workflow for onboarding, verification, access, or review.",
    icon: Workflow,
  },
  {
    title: "Connect providers",
    description:
      "Use IdentityCore services, third-party vendors, government APIs, or your own internal systems.",
    icon: Network,
  },
  {
    title: "Apply policies",
    description:
      "Control rules, thresholds, routing, manual review, retention, and country-specific requirements.",
    icon: GitBranch,
  },
  {
    title: "Run identity services",
    description:
      "Execute document intelligence, biometrics, liveness, consent, risk, audit, and evidence workflows.",
    icon: FileSearch,
  },
  {
    title: "Return decisions",
    description:
      "Send results back through dashboards, webhooks, APIs, reports, or manual review queues.",
    icon: BellRing,
  },
];

export function HowItWorksPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/how-it-works" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[640px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                How it works
              </Badge>

              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Identity workflows from request to trusted decision.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                IdentityCore sits between your applications, providers,
                policies, and data systems. It orchestrates the workflow while
                your organization stays in control.
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
                    View API docs
                  </a>
                </Button>
              </div>
            </div>

            <FlowPreview />
          </div>
        </section>

        <Section>
          <SectionHeader
            eyebrow="Workflow lifecycle"
            title="One flow. Multiple services. Complete control."
            description="Every workflow follows the same foundation: define what should happen, route work to the right providers, apply policies, and return an auditable result."
          />

          <div className="mt-12 grid gap-6 lg:grid-cols-5">
            {steps.map((step, index) => (
              <WorkflowStepCard key={step.title} index={index} {...step} />
            ))}
          </div>
        </Section>

        <Section variant="dark">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <SectionHeader
              eyebrow="Provider orchestration"
              title="Bring your own systems without rebuilding the workflow."
              description="Swap OCR, face matching, liveness, risk, or government identity providers without changing the customer-facing experience or business workflow."
              variant="dark"
            />

            <ProviderRoutingList />
          </div>
        </Section>

        <Section variant="muted">
          <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <SectionHeader
              eyebrow="Built for different teams"
              title="Developers integrate. Operations configure. Reviewers decide."
              description="IdentityCore gives technical and non-technical teams one shared platform for building and operating identity workflows."
            />

            <TeamCardGrid />
          </div>
        </Section>

        <Section>
          <SectionHeader
            eyebrow="What you can build"
            title="Identity workflows for many products and industries."
          />

          <UseCaseGrid />
        </Section>

        <Section className="border-t">
          <SectionHeader
            title="Start from a workflow, not a blank system."
            description="Use templates, connect providers, configure policies, and publish identity workflows through APIs or hosted links."
            centered
          />

          <div className="mt-10 flex justify-center gap-3">
            <Button asChild size="lg" className="rounded-xl">
              <Link href="/templates">
                Browse templates
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="rounded-xl">
              <Link href="/platform">Explore platform</Link>
            </Button>
          </div>
        </Section>
      </main>

      <MarketingFooter />
    </div>
  );
}
