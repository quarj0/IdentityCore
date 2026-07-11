"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Input, Label } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, type Project } from "@/lib/dashboard-api";

export function LiveProjectDetailPage({ id, settings = false }: { id: string; settings?: boolean }) {
  const [project, setProject] = useState<Project | null>(null);
  const [name, setName] = useState("");
  const [origins, setOrigins] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const result = await dashboardApi.project(id);
    setProject(result);
    setName(result.name);
    setOrigins(result.allowed_origins.join(", "));
  }, [id]);

  useEffect(() => {
    dashboardApi.project(id).then((result) => {
      setProject(result); setName(result.name); setOrigins(result.allowed_origins.join(", "));
    }).catch((error) => setMessage(error.message));
  }, [id]);

  async function save() {
    setBusy("save");
    try {
      await dashboardApi.patchProject(id, {
        name,
        allowed_origins: origins.split(",").map((value) => value.trim()).filter(Boolean),
      });
      await load();
      setMessage("Project settings saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save project.");
    } finally { setBusy(""); }
  }

  async function toggleStatus() {
    if (!project) return;
    setBusy("status");
    try {
      await dashboardApi.projectAction(id, project.status === "suspended" ? "reactivate" : "suspend");
      await load();
      setMessage(project.status === "suspended" ? "Project reactivated." : "Project suspended.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to update project.");
    } finally { setBusy(""); }
  }

  return (
    <div className="space-y-8">
      <PageHeading title={settings ? "Project settings" : project?.name ?? "Project"} description={`Project ID: ${id}`} />
      {message ? <p role="status" className="rounded-xl bg-slate-50 p-3 text-sm text-slate-700">{message}</p> : null}
      {!project ? <p className="text-sm text-slate-500">Loading project...</p> : (
        <>
          <Card><CardContent className="grid gap-5 p-6 sm:grid-cols-2">
            <div><p className="text-xs uppercase text-slate-500">Environment</p><p className="mt-1 capitalize">{project.environment}</p></div>
            <div><p className="text-xs uppercase text-slate-500">Status</p><div className="mt-1"><StatusBadge status={project.status} /></div></div>
            <div><p className="text-xs uppercase text-slate-500">Slug</p><p className="mt-1">{project.slug}</p></div>
            <div><p className="text-xs uppercase text-slate-500">Created</p><p className="mt-1">{new Date(project.created_at).toLocaleString()}</p></div>
          </CardContent></Card>
          <Card><CardContent className="space-y-5 p-6">
            <div><Label htmlFor="project-name">Project name</Label><Input id="project-name" className="mt-2" value={name} onChange={(event) => setName(event.target.value)} /></div>
            <div><Label htmlFor="allowed-origins">Allowed origins</Label><Input id="allowed-origins" className="mt-2" value={origins} onChange={(event) => setOrigins(event.target.value)} placeholder="https://app.example.com, https://admin.example.com" /><p className="mt-2 text-xs text-slate-500">Comma-separated HTTPS origins.</p></div>
            <div className="flex flex-wrap gap-3"><Button onClick={save} disabled={!name.trim() || Boolean(busy)}>{busy === "save" ? "Saving..." : "Save settings"}</Button><Button variant="outline" asChild><Link href={`/workflows?project=${project.id}`}>View workflows</Link></Button><Button variant="destructive" onClick={toggleStatus} disabled={Boolean(busy)}>{project.status === "suspended" ? "Reactivate project" : "Suspend project"}</Button></div>
          </CardContent></Card>
        </>
      )}
    </div>
  );
}
