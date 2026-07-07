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

      <main>
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

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                Workflow lifecycle
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                One flow. Multiple services. Complete control.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                Every workflow follows the same foundation: define what should
                happen, route work to the right providers, apply policies, and
                return an auditable result.
              </p>
            </div>

            <div className="mt-12 grid gap-6 lg:grid-cols-5">
              {steps.map((step, index) => (
                <WorkflowStepCard key={step.title} index={index} {...step} />
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Provider orchestration
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Bring your own systems without rebuilding the workflow.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                Swap OCR, face matching, liveness, risk, or government identity
                providers without changing the customer-facing experience or
                business workflow.
              </p>
            </div>

            <ProviderRoutingList />
          </div>
        </section>

        <section className="bg-slate-50 py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-600">
                Built for different teams
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Developers integrate. Operations configure. Reviewers decide.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                IdentityCore gives technical and non-technical teams one shared
                platform for building and operating identity workflows.
              </p>
            </div>

            <TeamCardGrid />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">
                What you can build
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Identity workflows for many products and industries.
              </h2>
            </div>

            <UseCaseGrid />
          </div>
        </section>

        <section className="border-t py-24">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <h2 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Start from a workflow, not a blank system.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
              Use templates, connect providers, configure policies, and publish
              identity workflows through APIs or hosted links.
            </p>

            <div className="mt-10 flex justify-center gap-3">
              <Button asChild size="lg" className="rounded-xl">
                <Link href="/templates">
                  Browse templates
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="rounded-xl"
              >
                <Link href="/platform">Explore platform</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
