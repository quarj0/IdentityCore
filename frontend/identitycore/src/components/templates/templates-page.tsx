import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";
import { Badge, Button } from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { TemplateCard } from "@/components/marketing/template-card";
import { workflowTemplates } from "@/data/templates";

const filters = [
  "All",
  "Government",
  "Financial services",
  "Education",
  "Healthcare",
  "HR",
  "General",
];

const productionSteps = [
  "Clone official workflow",
  "Customize providers and policy rules",
  "Publish as hosted link or API workflow",
  "Monitor outcomes and audit history",
];

export function TemplatesPageContent() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/templates" />

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto max-w-7xl px-6 py-24 lg:py-32">
            <div className="max-w-4xl">
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Workflow templates
              </Badge>

              <h1 className="mt-6 text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Start with proven identity workflows.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                Choose a template, customize providers and policies, then
                publish it as an API workflow or hosted verification link.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
                <Button asChild size="lg" className="rounded-xl">
                  <Link href="/register">
                    Use a template
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
          </div>
        </section>

        <section className="border-y bg-slate-50 py-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm lg:w-96">
              <Search className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Search templates...
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {filters.map((filter) => (
                <span
                  key={filter}
                  className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-muted-foreground shadow-sm"
                >
                  {filter}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {workflowTemplates.map((template) => (
                <TemplateCard key={template.title} {...template} />
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-medium text-blue-300">
                From template to production
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                Templates are starting points, not locked workflows.
              </h2>
              <p className="mt-5 text-lg leading-8 text-slate-300">
                Every template can be cloned into your workspace, edited in the
                builder, connected to your providers, and published to your
                applications.
              </p>
            </div>

            <div className="grid gap-3">
              {productionSteps.map((item, index) => (
                <div
                  key={item}
                  className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/20 text-sm font-semibold text-blue-200">
                    {index + 1}
                  </div>
                  <p className="text-sm font-medium text-slate-100">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
