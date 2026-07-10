"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { dashboardApi, Policy } from "@/lib/dashboard-api";

export function LiveTemplatesPage() {
  const [items, setItems] = useState<Policy[]>([]); const [error, setError] = useState("");
  const load = () => dashboardApi.policies().then(setItems).catch(() => setError("Templates could not be loaded."));
  useEffect(() => { void load(); }, []);
  async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); await dashboardApi.createPolicy({ name: data.get("name"), description: data.get("description"), required_document_types: ["national_id"], required_liveness_level: "passive", face_match_threshold: "0.8500", manual_review_threshold: "0.6500", verification_expiry_minutes: 1440, media_retention_days: 30, metadata_retention_days: 365 }); event.currentTarget.reset(); load(); }
  return <div className="space-y-6"><div><h1 className="text-2xl font-semibold">Verification templates</h1><p className="text-slate-600">Versioned verification policies used by hosted requests.</p></div>{error ? <p className="text-red-600">{error}</p> : null}<Card><CardHeader><CardTitle>New draft</CardTitle></CardHeader><CardContent><form onSubmit={create} className="grid gap-3 md:grid-cols-3"><div><Label>Name</Label><Input name="name" required /></div><div><Label>Description</Label><Input name="description" /></div><Button className="self-end">Create draft</Button></form></CardContent></Card><div className="grid gap-3">{items.map(item => <Link key={item.id} href={`/templates/${item.id}`} className="rounded-2xl border bg-white p-4"><span className="font-medium">{item.name} v{item.version}</span><span className="ml-3 text-sm text-slate-500">{item.status}</span></Link>)}</div></div>;
}
