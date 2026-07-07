import Link from "next/link";
import { ArrowRight, Code2 } from "lucide-react";
import { Badge, Button } from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/footer";
import { SolutionGrid } from "@/components/solutions/solution-grid";
import { IndustryUseCase } from "@/components/solutions/industry-use-case";

export default function SolutionsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/solutions" />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[620px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto max-w-7xl px-6 py-24 lg:py-32">
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Solutions
            </Badge>

            <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
              Identity infrastructure for every organization that needs trust.
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
              IdentityCore helps governments, enterprises, and platforms build
              identity workflows using configurable policies, provider
              orchestration, APIs, templates, and secure governance.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
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
                <Link href="/platform">
                  <Code2 className="h-4 w-4" />
                  Explore platform
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="max-w-3xl">
              <p className="text-sm font-medium text-blue-600">Industries</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Build identity workflows for your market.
              </h2>
              <p className="mt-5 text-lg leading-8 text-muted-foreground">
                Start with common industry workflows, then customize providers,
                documents, thresholds, review logic, and deployment
                requirements.
              </p>
            </div>

            <SolutionGrid />
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                Same platform, different workflows
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Every industry needs trust, but not the same verification rules.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                A bank, university, hospital, and government agency may all need
                identity workflows, but each requires different policies,
                providers, documents, thresholds, and review processes.
              </p>
            </div>

            <IndustryUseCase />
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
            <div>
              <p className="text-sm font-medium text-blue-600">
                Why this matters
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Identity systems should adapt to the organization, not the other
                way around.
              </h2>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {[
                [
                  "Different policies",
                  "Configure workflows by risk, country, use case, and organization type.",
                ],
                [
                  "Different providers",
                  "Use IdentityCore services or connect existing government, AI, and internal systems.",
                ],
                [
                  "Different deployment needs",
                  "Start with hosted SaaS and grow toward private, hybrid, or dedicated infrastructure.",
                ],
                [
                  "Different teams",
                  "Give developers, operations, compliance, and reviewers tools that fit their work.",
                ],
              ].map(([title, description]) => (
                <div
                  key={title}
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <MarketingCTA
          title="Build identity workflows around your organization."
          description="Use IdentityCore to design policies, route providers, and operate trusted identity workflows across industries."
          secondaryHref="/how-it-works"
          secondaryLabel="See how it works"
        />
      </main>

      <MarketingFooter />
    </div>
  );
}
