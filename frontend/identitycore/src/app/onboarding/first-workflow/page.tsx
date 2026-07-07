import Link from "next/link";
import { ArrowRight, Workflow } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function FirstWorkflowPage() {
  return (
    <OnboardingPageShell
      eyebrow="First workflow"
      title="Create your first identity workflow."
      description="Start from an official workflow template or create a custom workflow for your organization."
      pathname="/onboarding/first-workflow"
    >
      <Card className="max-w-2xl rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <Workflow className="mb-4 h-7 w-7 text-blue-600" />
          <CardTitle>Start with templates</CardTitle>
          <CardDescription className="leading-7">
            Templates help you create onboarding, verification, access, and
            review workflows without starting from zero.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Button asChild size="lg" className="w-full rounded-xl sm:w-auto">
            <Link href="/templates">
              Browse templates
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </OnboardingPageShell>
  );
}
