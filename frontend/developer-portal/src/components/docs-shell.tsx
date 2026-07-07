"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { BrandMark, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, ThemeToggle, cn } from "@identitycore/ui";
import { dashboardUrl, docGroups, productSiteUrl, type DocPage } from "@/lib/docs-content";

export function DocsShell({ page }: { page: DocPage }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[280px_minmax(0,1fr)_420px]">
        <aside className="border-r border-border bg-card px-5 py-6">
          <div className="sticky top-6 space-y-8">
            <Link href="/quickstart">
              <BrandMark subtitle="Developer portal" />
            </Link>

            <div className="rounded-lg border border-border bg-muted/40 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <ShieldCheck className="h-4 w-4 text-primary" />
                Production checklist
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Use secret keys on the server, keep policies versioned, and subscribe to verification status webhooks before launch.
              </p>
            </div>

            <nav className="space-y-6">
              {docGroups.map((group) => (
                <div key={group.title}>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {group.title}
                  </div>
                  <div className="space-y-0.5">
                    {group.items.map((item) => {
                      const active = pathname === item.path;
                      return (
                        <Link
                          key={item.path}
                          href={item.path}
                          className={cn(
                            "flex items-center justify-between rounded-md px-3 py-2 text-sm transition-colors",
                            active
                              ? "bg-primary font-medium text-primary-foreground"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          )}
                        >
                          <span>{item.label}</span>
                          <ChevronRight className="h-3.5 w-3.5 opacity-50" />
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>

            <div className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
              <span className="text-xs text-muted-foreground">Theme</span>
              <ThemeToggle />
            </div>
          </div>
        </aside>

        <main id="main-content" className="px-6 py-8 lg:px-10 xl:px-14">
          <div className="mx-auto max-w-4xl space-y-8">
            <section className="space-y-4">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight">{page.title}</h1>
                <p className="mt-2 max-w-3xl text-muted-foreground leading-7">{page.description}</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <a href={dashboardUrl}>Open dashboard</a>
                </Button>
                <Button asChild variant="outline">
                  <a href={productSiteUrl}>Back to product site</a>
                </Button>
              </div>
            </section>

            <section className="space-y-4">
              {page.sections.map((section) => (
                <Card key={section.heading}>
                  <CardHeader>
                    <CardTitle className="text-lg">{section.heading}</CardTitle>
                    <CardDescription className="text-sm leading-6">{section.body}</CardDescription>
                  </CardHeader>
                  {section.code ? (
                    <CardContent>
                      <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-xs leading-6 text-foreground">
                        <code>{section.code}</code>
                      </pre>
                    </CardContent>
                  ) : null}
                </Card>
              ))}
            </section>
          </div>
        </main>

        <aside className="border-l border-border bg-muted/20 px-5 py-8">
          <div className="sticky top-8 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">On this page</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {page.sections.map((section) => (
                  <div key={section.heading} className="text-sm text-muted-foreground">
                    {section.heading}
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Portal posture</CardTitle>
                <CardDescription>Static-first docs with route-driven content.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                Documentation routes map directly to product areas so API, workflow, and operational guidance can grow without rewriting the shell.
              </CardContent>
            </Card>
          </div>
        </aside>
      </div>
    </div>
  );
}
