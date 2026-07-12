"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Checkbox, Input, Label } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, type Organization, type WorkflowDefinition } from "@/lib/dashboard-api";

const availableSteps = ["consent", "document", "selfie", "liveness", "face_match", "decision", "manual_review", "webhook"];

export function LiveWorkflowDetailPage({ id, builder = false }: { id: string; builder?: boolean }) {
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<string[]>([]);
  const [settings, setSettings] = useState<Record<string, string | number | boolean>>({});
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [organization, setOrganization] = useState<Organization | null>(null);

  const load = useCallback(async () => {
    const result = await dashboardApi.workflow(id);
    setWorkflow(result); setName(result.name); setDescription(result.description);
    setSteps(result.steps); setSettings(result.settings as Record<string, string | number | boolean>);
  }, [id]);
  useEffect(() => {
    dashboardApi.workflow(id).then((result) => {
      setWorkflow(result); setName(result.name); setDescription(result.description);
      setSteps(result.steps); setSettings(result.settings as Record<string, string | number | boolean>);
    }).catch((error) => setMessage(error.message));
  }, [id]);
  useEffect(() => { dashboardApi.organization().then(setOrganization).catch(() => undefined); }, []);

  function toggleStep(step: string, enabled: boolean) {
    setSteps((current) => enabled ? [...current, step] : current.filter((value) => value !== step));
  }

  async function save() {
    setBusy("save");
    try {
      await dashboardApi.patchWorkflow(id, { name, description, steps, settings });
      await load(); setMessage("Workflow draft saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to save workflow."); }
    finally { setBusy(""); }
  }

  async function action(value: "publish" | "clone" | "archive") {
    setBusy(value);
    try {
      const result = await dashboardApi.workflowAction(id, value);
      if (value === "clone") window.location.assign(`/workflows/${result.id}`);
      else { await load(); setMessage(value === "publish" ? "Workflow published." : "Workflow archived."); }
    } catch (error) { setMessage(error instanceof Error ? error.message : "Workflow action failed."); }
    finally { setBusy(""); }
  }

  return (
    <div className="space-y-8">
      <PageHeading title={builder ? "Workflow builder" : workflow?.name ?? "Workflow"} description={builder ? "Configure steps, thresholds, retention, and publication." : `Workflow ID: ${id}`} />
      {message ? <p role="status" className="rounded-xl bg-slate-50 p-3 text-sm">{message}</p> : null}
      {!workflow ? <p className="text-sm text-slate-500">Loading workflow...</p> : <>
        <div className="flex items-center justify-between"><StatusBadge status={workflow.status} /><span className="text-sm text-slate-500">{workflow.current_version === 0 ? "Unpublished draft · version 0" : `Published version ${workflow.current_version}`}</span></div>
        {organization?.sandbox_usage.pending_approval ? <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">You can edit and test this sandbox draft. Publishing and cloning unlock after platform approval.</p> : null}
        <Card><CardContent className="grid gap-5 p-6 md:grid-cols-2">
          <div><Label htmlFor="workflow-name">Name</Label><Input id="workflow-name" className="mt-2" value={name} onChange={(event) => setName(event.target.value)} /></div>
          <div><Label htmlFor="workflow-description">Description</Label><Input id="workflow-description" className="mt-2" value={description} onChange={(event) => setDescription(event.target.value)} /></div>
        </CardContent></Card>
        <Card><CardContent className="p-6"><h2 className="font-semibold">Verification steps</h2><p className="mt-1 text-sm text-slate-500">Steps run in the order shown below. Consent and decision are required.</p><div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{availableSteps.map((step, index) => <label key={step} className="flex items-center gap-3 rounded-xl border p-4"><Checkbox checked={steps.includes(step)} disabled={step === "consent" || step === "decision"} onCheckedChange={(checked) => toggleStep(step, checked === true)} /><span className="text-sm capitalize">{index + 1}. {step.replaceAll("_", " ")}</span></label>)}</div></CardContent></Card>
        <Card><CardContent className="grid gap-5 p-6 md:grid-cols-3">
          {[ ["face_match_threshold", "Face-match threshold", "0.85"], ["manual_review_threshold", "Manual-review threshold", "0.65"], ["verification_expiry_minutes", "Expiry (minutes)", "1440"], ["media_retention_days", "Media retention (days)", "30"], ["metadata_retention_days", "Metadata retention (days)", "365"] ].map(([key, label, fallback]) => <div key={key}><Label htmlFor={key}>{label}</Label><Input id={key} type="number" step={key.includes("threshold") ? "0.01" : "1"} className="mt-2" value={String(settings[key] ?? fallback)} onChange={(event) => setSettings({...settings, [key]: Number(event.target.value)})} /></div>)}
        </CardContent></Card>
        <div className="flex flex-wrap gap-3"><Button onClick={save} disabled={Boolean(busy) || !name.trim()}>{busy === "save" ? "Saving..." : "Save draft"}</Button><Button onClick={() => action("publish")} disabled={Boolean(busy) || organization?.sandbox_usage.pending_approval}>{busy === "publish" ? "Publishing..." : "Publish version"}</Button><Button variant="outline" onClick={() => action("clone")} disabled={Boolean(busy) || organization?.sandbox_usage.pending_approval}>Clone</Button><Button variant="outline" asChild><Link href={`/workflows/${id}/versions`}>Version history</Link></Button><Button variant="destructive" onClick={() => action("archive")} disabled={Boolean(busy)}>Archive</Button></div>
      </>}
    </div>
  );
}
