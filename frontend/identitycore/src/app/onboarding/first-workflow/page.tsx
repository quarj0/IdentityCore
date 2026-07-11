"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Loader2, Workflow } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { restRequest } from "@/lib/api-client";

type WorkspaceWorkflow = { id: string; name: string; description: string; status: string };
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export default function FirstWorkflowPage() {
  const [workflows, setWorkflows] = useState<WorkspaceWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { restRequest<{ results: WorkspaceWorkflow[] }>("/workflows/").then((data) => setWorkflows(data.results)).catch(() => setWorkflows([])).finally(() => setLoading(false)); }, []);
  const selected = workflows[0];

  return <OnboardingPageShell eyebrow="First workflow" title={selected ? "Your first workflow is ready." : "Create your first identity workflow."}
    description={selected ? "Your chosen workflow is already part of this workspace. Continue in the dashboard to configure or test it." : "Start from an official workflow template or create a custom workflow for your organization."}
    pathname="/onboarding/first-workflow">
    <Card className="max-w-2xl rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
      <CardHeader>
        {loading ? <Loader2 className="mb-4 h-7 w-7 animate-spin text-blue-600" /> : selected ? <CheckCircle2 className="mb-4 h-7 w-7 text-emerald-600" /> : <Workflow className="mb-4 h-7 w-7 text-blue-600" />}
        <CardTitle>{selected ? selected.name : "Start with templates"}</CardTitle>
        <CardDescription className="leading-7">{selected ? selected.description || `Workflow status: ${selected.status}.` : "Templates help you create onboarding, verification, access, and review workflows without starting from zero."}</CardDescription>
      </CardHeader>
      <CardContent><Button asChild size="lg" className="w-full rounded-xl sm:w-auto"><Link href={selected ? `${DASHBOARD_URL}/workflows/${selected.id}` : "/templates"}>{selected ? "Open workflow in dashboard" : "Browse templates"}<ArrowRight className="h-4 w-4" /></Link></Button></CardContent>
    </Card>
  </OnboardingPageShell>;
}
