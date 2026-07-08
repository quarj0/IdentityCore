import { CheckCircle2, CircleDashed } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { onboardingSteps } from "@/data/mock-dashboard";

export function OnboardingProgress() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Workspace onboarding</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {onboardingSteps.map((step) => {
          const complete = step.status === "complete";
          const current = step.status === "current";

          return (
            <div key={step.title} className="flex gap-3">
              {complete ? (
                <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-blue-600" />
              ) : (
                <CircleDashed
                  className={
                    current
                      ? "mt-1 h-5 w-5 shrink-0 text-blue-600"
                      : "mt-1 h-5 w-5 shrink-0 text-slate-400"
                  }
                />
              )}

              <div>
                <p className="text-sm font-medium">{step.title}</p>
                <p className="text-sm leading-6 text-slate-600">
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
