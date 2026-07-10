"use client";

import { useEffect, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { dashboardApi, Policy } from "@/lib/dashboard-api";

export function LiveTemplateDetail({ id }: { id: string }) {
  const [item, setItem] = useState<Policy | null>(null); const [message, setMessage] = useState("");
  useEffect(() => { void dashboardApi.policy(id).then(setItem).catch(() => setMessage("Template could not be loaded.")); }, [id]);
  async function act(action: "clone" | "activate" | "archive") { const result = await dashboardApi.policyAction(id, action); setMessage(`${result.name} v${result.version} is ${result.status}.`); if (action !== "clone") setItem(result); }
  if (!item) return <p>{message || "Loading template…"}</p>;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">{item.name} v{item.version}</h1>{message ? <p>{message}</p> : null}<Card><CardHeader><CardTitle>Requirements</CardTitle></CardHeader><CardContent className="space-y-2"><p>Documents: {item.required_document_types.join(", ")}</p><p>Liveness: {item.required_liveness_level}</p><p>Face threshold: {item.face_match_threshold}</p><div className="flex gap-2 pt-3"><Button onClick={() => act("clone")}>Clone version</Button>{item.status === "draft" ? <Button onClick={() => act("activate")}>Activate</Button> : null}{item.status !== "archived" ? <Button variant="outline" onClick={() => act("archive")}>Archive</Button> : null}</div></CardContent></Card></div>;
}
