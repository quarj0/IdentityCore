"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  Download,
  FileJson,
  FileText,
  Loader2,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, VerificationDetail } from "@/lib/dashboard-api";
import { downloadAuthenticatedFile } from "@/lib/backend";

const TERMINAL_STATUSES = new Set(["verified", "rejected", "cancelled", "failed", "expired"]);

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

function subjectOf(item: VerificationDetail) {
  return item.verification_subject ?? item.subject ?? { full_name: "", email: "" };
}

function readable(value: string) {
  return value.replaceAll("_", " ");
}

export function LiveVerificationDetail({ id, review = false }: { id: string; review?: boolean }) {
  const [item, setItem] = useState<VerificationDetail | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      setItem(await dashboardApi.verification(id));
    } catch (caught) {
      setError(messageOf(caught));
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const isTerminal = Boolean(item && TERMINAL_STATUSES.has(item.status));
  const canReview = Boolean(
    review && item?.status === "manual_review_required" && !item.decision,
  );
  const canManageRequest = Boolean(item && !isTerminal && !item.decision);

  async function runAction(name: string, action: () => Promise<void>) {
    if (busy) return;
    setBusy(name);
    setMessage("");
    setError("");
    try {
      await action();
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function resend() {
    await runAction("resend", async () => {
      const result = await dashboardApi.resendVerification(id);
      await navigator.clipboard.writeText(result.verification_url);
      setMessage("A new verification link was issued, queued for delivery, and copied.");
    });
  }

  async function cancel() {
    if (!window.confirm("Cancel this verification? This action cannot be reversed.")) return;
    await runAction("cancel", async () => {
      await dashboardApi.cancelVerification(id, "Cancelled from dashboard");
      setMessage("Verification cancelled. No further review actions are available.");
    });
  }

  async function decide(decision: "verified" | "rejected" | "manual_review_required") {
    const trimmedReason = reason.trim();
    if (!trimmedReason) {
      setError("Enter a clear decision reason before submitting.");
      return;
    }
    const label =
      decision === "verified"
        ? "approve"
        : decision === "rejected"
          ? "reject"
          : "request more review for";
    if (!window.confirm(`Confirm that you want to ${label} this verification?`)) return;

    await runAction(`decision:${decision}`, async () => {
      await dashboardApi.decideReview(id, decision, trimmedReason);
      setMessage("Decision recorded. This review is now locked.");
      setReason("");
    });
  }

  async function download(format: "json" | "pdf") {
    await runAction(`download:${format}`, async () => {
      const suffix = format === "pdf" ? "download.pdf" : "download";
      await downloadAuthenticatedFile(
        `/verifications/${id}/evidence-report/${suffix}`,
        `identitycore-evidence-${id}.${format}`,
      );
      setMessage(`Evidence ${format.toUpperCase()} downloaded securely.`);
    });
  }

  const checkEntries = useMemo(() => Object.entries(item?.checks ?? {}), [item]);

  if (!item && !error) {
    return <p className="text-sm text-slate-500">Loading verification…</p>;
  }
  if (!item) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-semibold">This review is not available in the organization dashboard</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const subject = subjectOf(item);

  return (
    <div className="space-y-6">
      <PageHeading
        title={subject.full_name || subject.email || "Verification"}
        description={`${item.purpose} · ${item.policy.name || "No template selected"} · ${item.id}`}
        action={<StatusBadge status={item.status} />}
      />

      {message ? (
        <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      ) : null}
      {error ? (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {isTerminal ? (
        <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-slate-700" />
          <div>
            <p className="font-semibold text-slate-950">Review closed</p>
            <p className="mt-1 text-sm text-slate-600">
              This verification is {readable(item.status)}. The decision and audit record are immutable.
            </p>
          </div>
        </div>
      ) : null}

      <section aria-label="Verification checks" className="grid gap-4 md:grid-cols-3">
        {checkEntries.map(([name, check]) => (
          <Card key={name} className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium capitalize text-slate-600">
                {readable(name)}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex items-end justify-between gap-3">
              <StatusBadge status={check.status} />
              {check.score != null ? (
                <p className="font-mono text-sm tabular-nums text-slate-700">{check.score}</p>
              ) : (
                <p className="text-xs text-slate-400">No score</p>
              )}
            </CardContent>
          </Card>
        ))}
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Case evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
              <div><dt className="text-slate-500">Subject</dt><dd className="mt-1 font-medium text-slate-950">{subject.full_name || "Unknown"}</dd></div>
              <div><dt className="text-slate-500">External reference</dt><dd className="mt-1 font-mono text-slate-800">{item.external_reference || "—"}</dd></div>
              <div><dt className="text-slate-500">Created</dt><dd className="mt-1 text-slate-800">{new Date(item.created_at).toLocaleString()}</dd></div>
              <div><dt className="text-slate-500">Expires</dt><dd className="mt-1 text-slate-800">{new Date(item.expires_at).toLocaleString()}</dd></div>
              <div><dt className="text-slate-500">Risk</dt><dd className="mt-1 text-slate-800">{item.risk_assessment ? `${item.risk_assessment.risk_level} · ${item.risk_assessment.risk_score}` : "Not assessed"}</dd></div>
              <div><dt className="text-slate-500">Decision</dt><dd className="mt-1 text-slate-800">{item.decision ? readable(item.decision.decision) : "Pending"}</dd></div>
            </dl>

            {item.decision ? (
              <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Decision rationale</p>
                <p className="mt-2 text-sm text-slate-800">{item.decision.reason_detail || "No rationale recorded."}</p>
                <p className="mt-2 text-xs text-slate-500">{new Date(item.decision.decided_at).toLocaleString()}</p>
              </div>
            ) : null}

            {item.evidence_report ? (
              <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-200 pt-5">
                <Button type="button" variant="outline" onClick={() => download("json")} disabled={Boolean(busy)}>
                  {busy === "download:json" ? <Loader2 className="size-4 animate-spin" /> : <FileJson className="size-4" />}
                  Download JSON
                </Button>
                <Button type="button" variant="outline" onClick={() => download("pdf")} disabled={Boolean(busy)}>
                  {busy === "download:pdf" ? <Loader2 className="size-4 animate-spin" /> : <FileText className="size-4" />}
                  Download PDF
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader><CardTitle>Request controls</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {canManageRequest ? (
              <>
                <Button type="button" onClick={resend} disabled={Boolean(busy)} className="w-full">
                  {busy === "resend" ? <Loader2 className="size-4 animate-spin" /> : <Copy className="size-4" />}
                  Issue fresh link
                </Button>
                <Button type="button" variant="outline" onClick={cancel} disabled={Boolean(busy)} className="w-full">
                  {busy === "cancel" ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
                  Cancel verification
                </Button>
              </>
            ) : (
              <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                Request controls are unavailable after a final decision.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {canReview ? (
        <Card className="rounded-2xl border-slate-300 shadow-sm">
          <CardHeader>
            <CardTitle>Record review decision</CardTitle>
            <p className="text-sm text-slate-500">One decision is allowed. The case locks immediately after submission.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="decision_reason">Decision rationale</Label>
              <Input
                id="decision_reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="State the evidence and policy basis for this decision"
                disabled={Boolean(busy)}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={() => decide("verified")} disabled={Boolean(busy)}>
                {busy === "decision:verified" ? <Loader2 className="size-4 animate-spin" /> : null}
                Approve
              </Button>
              <Button type="button" variant="destructive" onClick={() => decide("rejected")} disabled={Boolean(busy)}>
                {busy === "decision:rejected" ? <Loader2 className="size-4 animate-spin" /> : null}
                Reject
              </Button>
              <Button type="button" variant="outline" onClick={() => decide("manual_review_required")} disabled={Boolean(busy)}>
                {busy === "decision:manual_review_required" ? <Loader2 className="size-4 animate-spin" /> : <AlertTriangle className="size-4" />}
                Escalate review
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : review ? (
        <Card className="rounded-2xl border-slate-200 bg-slate-50 shadow-none">
          <CardContent className="flex items-start gap-3 py-5">
            <Download className="mt-0.5 size-5 text-slate-500" />
            <div>
              <p className="font-medium text-slate-900">No review action available</p>
              <p className="mt-1 text-sm text-slate-600">Only cases currently awaiting manual review can receive a decision.</p>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
