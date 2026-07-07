import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowRight,
  Check,
  Clock3,
  GitBranch,
  Layers3,
  ShieldCheck,
  Sparkles,
  Users,
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
import type { ReactNode } from "react";
import { RelatedTemplates } from "@/components/templates/related-templates";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { FeatureCard } from "@/components/marketing/feature-card";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";
import { getTemplate, workflowTemplates } from "@/data/templates";

const DASHBOARD_URL =
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export function generateStaticParams() {
  return workflowTemplates.map((template) => ({
    slugs: template.slug,
  }));
}

export default async function TemplateDetailPage({
  params,
}: {
  params: Promise<{ slugs: string }>;
}) {
  const { slugs } = await params;
  const template = getTemplate(slugs);

  if (!template) {
    notFound();
  }

  const Icon = template.icon;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/templates" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Official workflow template
              </Badge>

              <div className="mt-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <Icon className="h-6 w-6" />
              </div>

              <h1 className="mt-6 max-w-4xl text-5xl font-semibold tracking-tight sm:text-6xl lg:leading-[0.98]">
                {template.title}
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                {template.description}
              </p>

              <div className="mt-8 flex flex-wrap gap-2">
                {template.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-white px-4 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg" className="rounded-xl">
                  <a href={DASHBOARD_URL}>
                    Use this template
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-xl"
                >
                  <Link href="/templates">Back to templates</Link>
                </Button>
              </div>
            </div>

            <Card className="rounded-[2rem] border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
              <CardHeader className="border-b bg-slate-50/70">
                <CardTitle className="text-base">Workflow preview</CardTitle>
                <CardDescription>
                  Core steps for the {template.title.toLowerCase()} journey
                </CardDescription>
              </CardHeader>

              <CardContent className="p-6">
                <div className="space-y-3">
                  {template.steps.map((step, index) => (
                    <div key={step}>
                      <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-sm font-semibold text-blue-700">
                          {index + 1}
                        </div>
                        <p className="text-sm font-medium">{step}</p>
                      </div>
                      {index < template.steps.length - 1 ? (
                        <div className="ml-9 h-5 w-px bg-slate-200" />
                      ) : null}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <Section>
          <div className="grid gap-6 lg:grid-cols-3">
            <InfoCard
              icon={<Sparkles className="h-5 w-5" />}
              title="Template highlights"
              items={template.highlights}
            />
            <InfoCard
              icon={<Check className="h-5 w-5" />}
              title="Required inputs"
              items={template.required}
            />
            <InfoCard
              icon={<Layers3 className="h-5 w-5" />}
              title="Provider services"
              items={template.providers}
            />
            <InfoCard
              icon={<GitBranch className="h-5 w-5" />}
              title="Policy rules"
              items={template.policies}
            />
          </div>
        </Section>

        <Section variant="muted">
          <div className="grid gap-6 lg:grid-cols-[0.78fr_1.22fr]">
              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                    <Users className="h-5 w-5" />
                  </div>
                  <CardTitle>Who this is for</CardTitle>
                  <CardDescription className="leading-7">
                    {template.audience}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 px-6 pb-6">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-medium text-slate-900">
                      Expected outcome
                    </p>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {template.outcome}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
                      <Clock3 className="h-4 w-4 text-blue-600" />
                      Launch profile
                    </div>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {template.turnaround}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle>Launch checklist</CardTitle>
                  <CardDescription>
                    The operational work most teams finish before publishing
                    this workflow.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 px-6 pb-6 sm:grid-cols-2">
                  {template.launchChecklist.map((item, index) => (
                    <div key={item}>
                      <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-blue-600">
                        Item {index + 1}
                      </p>
                      <FeatureCard
                        title={item}
                        description="Operational setup to complete before publishing this workflow."
                        icon={Check}
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
          </div>
        </Section>

        <Section variant="dark">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <SectionHeader
              eyebrow="Customizable workflow"
              title="Clone it, adjust it, and connect your own providers."
              description="This template is only a starting point. Your organization can change document requirements, thresholds, review logic, retention rules, provider routing, and webhook behavior."
              variant="dark"
            />

            <div className="grid gap-3">
              {template.whyItMatters.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <ShieldCheck className="h-5 w-5 text-blue-300" />
                  <span className="text-sm font-medium text-slate-100">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Section>

        <RelatedTemplates currentSlug={template.slug} category={template.category} />

        <MarketingCTA
          title="Start from a template, then make it yours."
          description="Use official workflows as the foundation for your organization's identity infrastructure."
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
  icon: ReactNode;
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
