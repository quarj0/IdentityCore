"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowRight, Search } from "lucide-react";
import { Badge, Button, Input, cn } from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
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
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");

  const filteredTemplates = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return workflowTemplates.filter((template) => {
      const matchesFilter =
        activeFilter === "All" || template.category === activeFilter;

      const matchesQuery =
        normalizedQuery.length === 0 ||
        template.title.toLowerCase().includes(normalizedQuery) ||
        template.description.toLowerCase().includes(normalizedQuery) ||
        template.category.toLowerCase().includes(normalizedQuery) ||
        template.tags.some((tag) =>
          tag.toLowerCase().includes(normalizedQuery),
        );

      return matchesFilter && matchesQuery;
    });
  }, [activeFilter, query]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/templates" />

      <main id="main-content">
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
            <div className="relative lg:w-96">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search templates..."
                className="rounded-2xl border-slate-200 bg-white py-6 pl-11 shadow-sm"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              {filters.map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setActiveFilter(filter)}
                  className={cn(
                    "rounded-full border px-4 py-2 text-sm shadow-sm transition-colors",
                    activeFilter === filter
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-white text-muted-foreground hover:border-blue-200 hover:text-blue-700",
                  )}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="mx-auto max-w-7xl px-6">
            {filteredTemplates.length > 0 ? (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredTemplates.map((template) => (
                  <TemplateCard key={template.title} {...template} />
                ))}
              </div>
            ) : (
              <div className="rounded-[2rem] border border-slate-200 bg-slate-50 px-6 py-16 text-center">
                <p className="text-lg font-semibold">No templates found</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Try a different search term or choose another category.
                </p>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-6 rounded-xl"
                  onClick={() => {
                    setQuery("");
                    setActiveFilter("All");
                  }}
                >
                  Reset filters
                </Button>
              </div>
            )}
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

      <MarketingFooter />
    </div>
  );
}
