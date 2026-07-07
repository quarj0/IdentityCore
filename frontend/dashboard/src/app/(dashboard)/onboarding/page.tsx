import type { Metadata } from "next";
import { AlertTriangle, CheckCircle2, Clock3, FileCheck2, ShieldCheck } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  PageHeader,
  Progress,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Onboarding" };

const checklist = [
  { label: "Email verified", done: true },
  { label: "Organization profile completed", done: true },
  { label: "Verification documents uploaded", done: true },
  { label: "Security owner appointed", done: false },
  { label: "Production approval interview", done: false },
];

export default function OnboardingPage() {
  const completed = checklist.filter((item) => item.done).length;
  const progress = (completed / checklist.length) * 100;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organization onboarding"
        description="Track approval readiness, remaining setup tasks, and production access status."
        actions={
          <>
            <Button variant="outline">Open profile</Button>
            <Button>Request production review</Button>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Readiness</CardTitle>
                <CardDescription>Current onboarding completion toward production approval.</CardDescription>
              </div>
              <Badge variant="warning">Pending review</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Completion</span>
                <span className="font-medium">{completed} of {checklist.length} tasks</span>
              </div>
              <Progress value={progress} />
            </div>

            <div className="space-y-3">
              {checklist.map((item) => (
                <div key={item.label} className="flex items-start gap-3 rounded-lg border border-border p-4">
                  {item.done ? (
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  ) : (
                    <Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                  )}
                  <div className="text-sm">
                    <div className="font-medium text-foreground">{item.label}</div>
                    <div className="text-muted-foreground">
                      {item.done ? "Completed and ready for production review." : "Still required before full approval."}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Current status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-start gap-3 rounded-lg bg-amber-500/10 p-3 text-amber-800 dark:text-amber-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                Security owner is missing, so production access is still blocked.
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-blue-500/10 p-3 text-blue-800 dark:text-blue-200">
                <FileCheck2 className="mt-0.5 h-4 w-4 shrink-0" />
                Submitted business registration and website review passed initial checks.
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Next best actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
              <div className="flex gap-3">
                <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-primary" />
                Assign an internal security owner and confirm incident response coverage.
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-primary" />
                Validate webhook endpoints and create at least one production policy.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
