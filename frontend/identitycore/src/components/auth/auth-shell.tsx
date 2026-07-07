import type { ReactNode } from "react";
import { cn } from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

interface AuthShellProps {
  badge: string;
  title: string;
  description: string;
  children: ReactNode;
  layout?: "split" | "stacked";
  sectionClassName?: string;
}

export function AuthShell({
  badge,
  title,
  description,
  children,
  layout = "split",
  sectionClassName,
}: AuthShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 -z-10 h-[720px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

        <section
          className={cn(
            "mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-24",
            sectionClassName,
          )}
        >
          {layout === "split" ? (
            <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
              <div>
                <p className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 ring-1 ring-slate-200">
                  {badge}
                </p>

                <h1 className="mt-6 max-w-4xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl lg:leading-[0.98]">
                  {title}
                </h1>

                <p className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground sm:text-lg">
                  {description}
                </p>
              </div>

              {children}
            </div>
          ) : (
            <div>
              <div className="max-w-3xl">
                <p className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 ring-1 ring-slate-200">
                  {badge}
                </p>

                <h1 className="mt-6 max-w-5xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl lg:leading-[0.98]">
                  {title}
                </h1>

                <p className="mt-6 max-w-3xl text-base leading-8 text-muted-foreground sm:text-lg">
                  {description}
                </p>
              </div>

              <div className="mt-12">{children}</div>
            </div>
          )}
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
