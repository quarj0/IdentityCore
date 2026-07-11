"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, Card, CardContent, Input } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, Organization, Project } from "@/lib/dashboard-api";

export function LiveProjectsPage() {
  const [items, setItems] = useState<Project[]>([]), [organization, setOrganization] = useState<Organization | null>(null), [name, setName] = useState(""), [error, setError] = useState("");
  const load = () => Promise.all([dashboardApi.projects(), dashboardApi.organization()]).then(([projects, org]) => { setItems(projects.results); setOrganization(org); }).catch((e) => setError(e.message));
  useEffect(() => { void load(); }, []);
  async function create() { try { await dashboardApi.createProject({ name, environment: "sandbox", allowed_origins: [] }); setName(""); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Unable to create project."); } }
  const limited = Boolean(organization?.sandbox_usage.pending_approval && items.length >= 1);
  return <div className="space-y-8"><PageHeading title="Projects" description="Isolated sandbox and production environments." />{error ? <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
    {limited ? <Card className="border-amber-200 bg-amber-50"><CardContent className="p-5 text-sm text-amber-900"><p className="font-semibold">Sandbox project ready</p><p className="mt-1">Pending workspaces are limited to this project. Production projects unlock after approval.</p></CardContent></Card> : <Card><CardContent className="flex gap-3 p-5"><Input aria-label="Project name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" /><Button disabled={!name.trim()} onClick={create}>Create sandbox</Button></CardContent></Card>}
    <div className="grid gap-4 md:grid-cols-2">{items.map((item) => <Link key={item.id} href={`/projects/${item.id}`}><Card className="h-full"><CardContent className="p-6"><h2 className="font-semibold">{item.name}</h2><p className="mt-2 text-sm capitalize text-slate-500">{item.environment} · {item.status}</p></CardContent></Card></Link>)}</div></div>;
}
