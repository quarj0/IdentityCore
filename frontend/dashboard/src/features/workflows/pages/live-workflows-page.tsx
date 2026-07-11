"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, Card, CardContent, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, type Project, type WorkflowDefinition } from "@/lib/dashboard-api";

const defaultSteps = ["consent", "document", "selfie", "liveness", "face_match", "decision", "manual_review", "webhook"];

export function LiveWorkflowsPage({ templateSlug = "" }: { templateSlug?: string }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [items, setItems] = useState<WorkflowDefinition[]>([]);
  const [project, setProject] = useState("");
  const [name, setName] = useState(() => templateSlug.split("-").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" "));
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi.projects().then(({ results }) => {
      setProjects(results);
      const saved = window.localStorage.getItem("identitycore.dashboard.project");
      setProject(results.some((item) => item.id === saved) ? saved! : results[0]?.id ?? "");
    }).catch((caught) => setError(caught.message));
  }, []);

  useEffect(() => {
    if (!project) return;
    dashboardApi.workflows(project).then(({ results }) => setItems(results)).catch((caught) => setError(caught.message));
  }, [project]);

  async function create() {
    try {
      const created = await dashboardApi.createWorkflow({ project_id: project, name, description: templateSlug ? `Created from the ${templateSlug} template.` : "", steps: defaultSteps, settings: templateSlug ? { template_slug: templateSlug } : {} });
      window.location.assign(`/workflows/${created.id}/builder`);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to create workflow."); }
  }

  return <div className="space-y-8"><PageHeading title="Workflows" description="Build and publish versioned identity verification flows." />{error ? <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}<Card><CardContent className="grid gap-3 p-5 md:grid-cols-[220px_1fr_auto]"><Select value={project} onValueChange={setProject}><SelectTrigger><SelectValue placeholder="Project" /></SelectTrigger><SelectContent>{projects.map((item) => <SelectItem key={item.id} value={item.id}>{item.name}</SelectItem>)}</SelectContent></Select><Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Workflow name" /><Button disabled={!project || !name.trim()} onClick={create}>Create workflow</Button></CardContent></Card><div className="grid gap-4 md:grid-cols-2">{items.map((item) => <Link key={item.id} href={`/workflows/${item.id}`}><Card className="h-full transition-shadow hover:shadow-md"><CardContent className="p-6"><h2 className="font-semibold">{item.name}</h2><p className="mt-2 text-sm capitalize text-slate-500">{item.status} · version {item.current_version}</p><p className="mt-3 text-sm text-slate-600">{item.description || `${item.steps.length} configured steps`}</p></CardContent></Card></Link>)}</div></div>;
}
