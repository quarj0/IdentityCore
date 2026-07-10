import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight, Check, GitBranch, Layers3, Workflow } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";
import { getSolution, solutions } from "@/data/solutions";

export function generateStaticParams() {
  return solutions.map((solution) => ({
    slug: solution.slug,
  }));
}

export default async function SolutionDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const solution = getSolution(slug);

  if (!solution) {
    notFound();
  }

  const Icon = solution.icon;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/solutions" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Solution
              </Badge>

              <div className="mt-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <Icon className="h-6 w-6" />
              </div>

              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:leading-[0.98]">
                Identity infrastructure for {solution.title.toLowerCase()}.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                {solution.description}
              </p>

              <div className="mt-8 flex flex-wrap gap-2">
                {solution.useCases.map((item) => (
                  <span
                    key={item}
                    className="rounded-full bg-white px-4 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200"
                  >
                    {item}
                  </span>
                ))}
              </div>

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
                  <Link href="/solutions">Back to solutions</Link>
                </Button>
              </div>
            </div>

            <Card className="rounded-4xl border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
              <CardHeader className="border-b bg-slate-50/70">
                <CardTitle className="text-base">Common workflows</CardTitle>
              </CardHeader>

              <CardContent className="space-y-3 p-6">
                {solution.workflows.map((workflow, index) => (
                  <div
                    key={workflow}
                    className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-sm font-semibold text-blue-700">
                      {index + 1}
                    </div>
                    <p className="text-sm font-medium">{workflow}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>

        <Section>
          <div className="grid gap-6 lg:grid-cols-3">
            <InfoCard
              icon={<Workflow className="h-5 w-5" />}
              title="Workflow model"
              items={solution.workflows}
            />
            <InfoCard
              icon={<Layers3 className="h-5 w-5" />}
              title="Capabilities"
              items={solution.capabilities}
            />
            <InfoCard
              icon={<GitBranch className="h-5 w-5" />}
              title="Why IdentityCore fits"
              items={[
                "Use templates or custom workflows",
                "Connect internal or external providers",
                "Control policies and review logic",
                "Keep audit and evidence records",
              ]}
            />
          </div>
        </Section>

        <Section variant="dark">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <SectionHeader
              eyebrow="Built for flexibility"
              title="Your industry defines the rules. IdentityCore runs the workflow."
              description="Use IdentityCore services, bring your own providers, or combine both through one policy-driven identity infrastructure layer."
              variant="dark"
            />

            <div className="grid gap-3">
              {[
                "Configure accepted documents",
                "Route work to selected providers",
                "Set review and approval thresholds",
                "Return results through dashboards or webhooks",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <Check className="h-5 w-5 text-blue-300" />
                  <span className="text-sm font-medium text-slate-100">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Section>

        <MarketingCTA
          title={`Build ${solution.title.toLowerCase()} identity workflows on IdentityCore.`}
          description="Start with infrastructure that supports workflows, policies, provider routing, APIs, and governance from day one."
          secondaryHref="/how-it-works"
          secondaryLabel="See how it works"
        />
      </main>

      <MarketingFooter />
    </div>
  );
}

function InfoCard({
  title,
  items,
  icon,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
}) {
  return (
    <Card className="rounded-3xl p-2 shadow-sm">
      <CardHeader>
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
          {icon}
        </div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3 px-6 pb-6">
        {items.map((item) => (
          <div key={item} className="flex gap-3 text-sm text-muted-foreground">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
            {item}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
