"use client";

import { use, useEffect, useState } from "react";
import { Card, CardContent } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, WorkflowDefinition } from "@/lib/dashboard-api";

type Version = { id: string; version: number; published_at: string };
export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { Promise.all([dashboardApi.workflow(id), dashboardApi.workflowVersions(id)]).then(([current, history]) => { setWorkflow(current); setVersions(history.results as Version[]); }).catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load workflow history.")); }, [id]);
  return <div className="space-y-8"><PageHeading title="Workflow history" description="Draft and immutable published versions" />{error ? <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p> : null}
    {workflow ? <div className="grid gap-3"><Card className="border-blue-200 bg-blue-50/40"><CardContent className="p-5"><div className="flex items-center justify-between"><div><p className="font-semibold">Current draft</p><p className="mt-1 text-sm text-slate-600">Version {workflow.current_version === 0 ? "0 (unpublished)" : `${workflow.current_version + 1} draft`} · {workflow.steps.length} configured steps</p></div><span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">{workflow.status}</span></div></CardContent></Card>
      {versions.length ? versions.map((version) => <Card key={version.id}><CardContent className="p-5"><p className="font-semibold">Published version {version.version}</p><p className="mt-1 text-sm text-slate-500">{new Date(version.published_at).toLocaleString()}</p></CardContent></Card>) : <p className="text-sm text-slate-500">No published versions yet. Pending workspaces can edit this draft; publishing unlocks after approval.</p>}</div> : <p className="text-sm text-slate-500">Loading history...</p>}
  </div>;
}
