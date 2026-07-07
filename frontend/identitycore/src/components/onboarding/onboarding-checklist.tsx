import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Badge, Button, Card, CardContent } from "@identitycore/ui";
import type { LucideIcon } from "lucide-react";

export interface OnboardingStep {
  title: string;
  description: string;
  status: "complete" | "current" | "upcoming";
  icon: LucideIcon;
  actionHref?: string;
  actionLabel?: string;
}

interface OnboardingChecklistProps {
  steps: OnboardingStep[];
}

export function OnboardingChecklist({
  steps,
}: OnboardingChecklistProps) {
  return (
    <div className="grid gap-4">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isComplete = step.status === "complete";
        const isCurrent = step.status === "current";

        return (
          <Card
            key={step.title}
            className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm"
          >
            <CardContent className="p-5">
              <div className="flex gap-4">
                <div
                  className={
                    isComplete
                      ? "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white"
                      : isCurrent
                        ? "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100"
                        : "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-500"
                  }
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold">{step.title}</h2>
                    <Badge
                      variant={isComplete || isCurrent ? "default" : "secondary"}
                      className="rounded-full"
                    >
                      {isComplete
                        ? "Complete"
                        : isCurrent
                          ? "Current"
                          : "Upcoming"}
                    </Badge>
                  </div>

                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    {step.description}
                  </p>
                </div>

                <div className="hidden text-sm text-muted-foreground sm:block">
                  Step {index + 1}
                </div>
              </div>

              {step.actionHref && step.actionLabel ? (
                <div className="mt-5 border-t pt-4">
                  <Button
                    asChild
                    size="sm"
                    variant={isCurrent ? "default" : "outline"}
                    className="rounded-xl"
                  >
                    <Link href={step.actionHref}>
                      {step.actionLabel}
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </Link>
                  </Button>
                </div>
              ) : null}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
