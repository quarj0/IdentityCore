import Link from "next/link";
import { ArrowRight, Cloud, Code2, GitBranch, Network, Users } from "lucide-react";
import { Badge, Button } from "@identitycore/ui";
import { FeatureCard } from "@/components/marketing/feature-card";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";
import { SolutionGrid } from "@/components/solutions/solution-grid";
import { IndustryUseCase } from "@/components/solutions/industry-use-case";

const solutionFitReasons = [
  {
    title: "Different policies",
    description:
      "Configure workflows by risk, country, use case, and organization type.",
    icon: GitBranch,
  },
  {
    title: "Different providers",
    description:
      "Use IdentityCore services or connect existing government, AI, and internal systems.",
    icon: Network,
  },
  {
    title: "Different deployment needs",
    description:
      "Start with hosted SaaS and grow toward private, hybrid, or dedicated infrastructure.",
    icon: Cloud,
  },
  {
    title: "Different teams",
    description:
      "Give developers, operations, compliance, and reviewers tools that fit their work.",
    icon: Users,
  },
];

export default function SolutionsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/solutions" />

      <main id="main-content">
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

        <Section>
          <SectionHeader
            eyebrow="Industries"
            title="Build identity workflows for your market."
            description="Start with common industry workflows, then customize providers, documents, thresholds, review logic, and deployment requirements."
          />

          <SolutionGrid />
        </Section>

        <Section variant="dark">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <SectionHeader
              eyebrow="Same platform, different workflows"
              title="Every industry needs trust, but not the same verification rules."
              description="A bank, university, hospital, and government agency may all need identity workflows, but each requires different policies, providers, documents, thresholds, and review processes."
              variant="dark"
            />

            <IndustryUseCase />
          </div>
        </Section>

        <Section>
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
            <SectionHeader
              eyebrow="Why this matters"
              title="Identity systems should adapt to the organization, not the other way around."
            />

            <div className="grid gap-4 sm:grid-cols-2">
              {solutionFitReasons.map((reason) => (
                <FeatureCard key={reason.title} {...reason} />
              ))}
            </div>
          </div>
        </Section>

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
