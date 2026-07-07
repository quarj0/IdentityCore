import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingFooter } from "../marketing/marketing-footer";
import {
  onboardingSteps,
  getOnboardingStepIndex,
  onboardingStepPaths,
} from "@/components/onboarding/onboarding-steps";

interface OnboardingPageShellProps {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  pathname: string;
}

export function OnboardingPageShell({
  eyebrow,
  title,
  description,
  children,
  pathname,
}: OnboardingPageShellProps) {
  const currentIndex = getOnboardingStepIndex(pathname);
  const previousPath =
    currentIndex > 0 ? onboardingStepPaths[currentIndex - 1] : "/onboarding";
  const nextPath =
    currentIndex >= 0 && currentIndex < onboardingStepPaths.length - 1
      ? onboardingStepPaths[currentIndex + 1]
      : null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

        <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:py-20">
          <Link
            href={previousPath}
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            {currentIndex > 0 ? "Previous step" : "Back to onboarding"}
          </Link>

          <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
            <div>
              <p className="text-sm font-medium text-blue-600">{eyebrow}</p>

              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
                {title}
              </h1>

              <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
                {description}
              </p>

              <div className="mt-8">{children}</div>

              <div className="mt-8 flex flex-col gap-3 border-t pt-6 sm:flex-row sm:items-center sm:justify-between">
                <Button asChild variant="outline" className="rounded-xl">
                  <Link href={previousPath}>
                    <ArrowLeft className="h-4 w-4" />
                    {currentIndex > 0 ? "Previous step" : "Back to overview"}
                  </Link>
                </Button>

                {nextPath ? (
                  <Button asChild className="rounded-xl">
                    <Link href={nextPath}>
                      Continue to next step
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                ) : null}
              </div>
            </div>

            <div className="space-y-4">
              <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <Badge variant="secondary" className="w-fit rounded-full">
                    Onboarding flow
                  </Badge>
                  <CardTitle className="mt-2">Complete in one pass</CardTitle>
                  <CardDescription>
                    Move step by step without returning to the overview after
                    each page.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {onboardingSteps.map((step, index) => {
                    const stepPath = onboardingStepPaths[index];
                    const isActive = stepPath === pathname;

                    return (
                      <Link
                        key={step.title}
                        href={stepPath}
                        className={
                          isActive
                            ? "block rounded-2xl border border-blue-200 bg-blue-50 p-3"
                            : "block rounded-2xl border border-slate-200 bg-slate-50 p-3 transition-colors hover:border-blue-200 hover:bg-blue-50/50"
                        }
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-900">
                            {step.title}
                          </p>
                          <span className="text-xs text-muted-foreground">
                            Step {index + 1}
                          </span>
                        </div>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          {step.description}
                        </p>
                      </Link>
                    );
                  })}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
