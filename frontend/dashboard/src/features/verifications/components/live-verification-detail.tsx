"use client";
import { useCallback, useEffect, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from "@identitycore/ui";
import { dashboardApi, VerificationDetail } from "@/lib/dashboard-api";
export function LiveVerificationDetail({ id, review = false }: { id: string; review?: boolean }) {
  const [item, setItem] = useState<VerificationDetail | null>(null); const [message, setMessage] = useState(""); const [reason, setReason] = useState("");
  const load = useCallback(() => dashboardApi.verification(id).then(setItem).catch(() => setMessage("Verification could not be loaded.")), [id]); useEffect(() => { void load(); }, [load]);
  async function resend() { const result = await dashboardApi.resendVerification(id); await navigator.clipboard.writeText(result.verification_url); setMessage("A fresh link was emailed and copied. Previous links are invalid."); }
  async function decide(decision: string) { await dashboardApi.decideReview(id, decision, reason); setMessage("Decision recorded."); load(); }
  if (!item) return <p>{message || "Loading verification…"}</p>;
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">{item.subject.full_name || "Verification"}</h1><p>{item.status} · {item.policy.name || "No template"}</p>{message ? <p>{message}</p> : null}<div className="grid gap-4 md:grid-cols-3">{Object.entries(item.checks).map(([name, check]) => <Card key={name}><CardHeader><CardTitle className="capitalize">{name.replace("_", " ")}</CardTitle></CardHeader><CardContent>{check.status}{check.score != null ? ` · ${check.score}` : ""}</CardContent></Card>)}</div><div className="flex gap-2"><Button onClick={resend}>Resend fresh link</Button><Button variant="outline" onClick={() => dashboardApi.cancelVerification(id, "Cancelled from dashboard").then(load)}>Cancel</Button></div>{review ? <Card><CardHeader><CardTitle>Manual decision</CardTitle></CardHeader><CardContent className="space-y-3"><Input value={reason} onChange={event => setReason(event.target.value)} placeholder="Decision reason" /><div className="flex gap-2"><Button onClick={() => decide("verified")}>Approve</Button><Button variant="outline" onClick={() => decide("rejected")}>Reject</Button><Button variant="outline" onClick={() => decide("manual_review_required")}>Keep in review</Button></div></CardContent></Card> : null}</div>;
}
