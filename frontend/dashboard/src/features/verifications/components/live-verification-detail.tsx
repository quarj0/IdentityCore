"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Copy, Download, Loader2, RefreshCw } from "lucide-react";
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
import {
  idempotentSubmission,
  PendingIdempotentSubmission,
} from "@/lib/idempotent-submission";

import { backend } from "@/lib/backend";

import { AuthenticityEvidence } from "./authenticity-evidence";

function messageOf(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

function subjectOf(item: VerificationDetail) {
  return (
    item.verification_subject ?? item.subject ?? { full_name: "", email: "" }
  );
}

export function LiveVerificationDetail({
  id,
  review = false,
}: {
  id: string;
  review?: boolean;
}) {
  const [item, setItem] = useState<VerificationDetail | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [reasonCode, setReasonCode] = useState("");
  const reasonRules = item?.policy.review_reason_rules;
  const codes = [
    ...new Set(
      Object.values(reasonRules?.outcomes ?? {}).flatMap((rule) => rule.codes),
    ),
  ];
  const [busy, setBusy] = useState("");
  const pendingDecision = useRef<PendingIdempotentSubmission | null>(null);

  const load = useCallback(async () => {
    setError("");
    try {
      setItem(await dashboardApi.verification(id));
    } catch (caught) {
      setError(messageOf(caught));
    }
  }, [id]);

  useEffect(() => {
    dashboardApi
      .verification(id)
      .then(setItem)
      .catch((caught) => setError(messageOf(caught)));
  }, [id]);

  async function downloadEvidence(format: "json" | "pdf") {
    setBusy(`evidence-${format}`);
    setError("");
    try {
      const suffix = format === "pdf" ? ".pdf" : "";
      const blob = await backend.download(
        `/verifications/${encodeURIComponent(id)}/evidence-report/download${suffix}`,
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `verification-evidence.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function resend() {
    setBusy("resend");
    setMessage("");
    setError("");
    try {
      const result = await dashboardApi.resendVerification(id);
      await navigator.clipboard.writeText(result.verification_url);
      setMessage(
        "A fresh verification link was created, queued for delivery, and copied. Previous active links were revoked.",
      );
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function cancel() {
    setBusy("cancel");
    setMessage("");
    setError("");
    try {
      await dashboardApi.cancelVerification(id, "Cancelled from dashboard");
      setMessage("Verification cancelled.");
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function decide(decision: string) {
    setBusy(decision);
    setMessage("");
    setError("");
    try {
      const rule = reasonRules?.outcomes?.[decision];
      if (
        rule &&
        (!rule.codes.includes(reasonCode) ||
          (rule.notes_required && !reason.trim()))
      ) {
        throw new Error(
          "Choose a reason configured for this outcome and provide required notes.",
        );
      }
      if (item?.decision?.approval_status === "pending") {
        await dashboardApi.approveReview(
          id,
          decision,
          reasonCode || undefined,
          reason.trim(),
        );
        setMessage("Independent review completed.");
      } else {
        const reasonDetail = reason.trim();
        pendingDecision.current = idempotentSubmission(
          { verificationId: id, decision, reasonDetail, reasonCode },
          pendingDecision.current,
        );
        const result = await dashboardApi.decideReview(
          id,
          decision,
          reasonDetail,
          pendingDecision.current.key,
          reasonCode || "dashboard_manual_review",
        );
        pendingDecision.current = null;
        setMessage(
          result.approval_required
            ? "Decision proposed and awaiting an independent reviewer."
            : "Manual review decision recorded.",
        );
      }
      setReason("");
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  if (!item && !error) {
    return <p className="text-sm text-slate-500">Loading verification...</p>;
  }
  if (!item) {
    return (
      <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  const subject = subjectOf(item);

  return (
    <div className="space-y-8">
      <PageHeading
        title={subject.full_name || subject.email || "Verification"}
        description={`${item.purpose} · ${item.policy.name || "No template selected"}`}
        action={<StatusBadge status={item.status} />}
      />

      {item.simulation ? (
        <p
          className="rounded-xl border border-amber-200 bg-amber-50 p-4"
          role="status"
        >
          Sandbox simulation: {item.simulation.scenario}. This case contains
          artificial results.
        </p>
      ) : null}
      {message ? (
        <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(item.checks).map(([name, check]) => (
          <Card key={name} className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="capitalize">
                {name.replaceAll("_", " ")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <StatusBadge status={check.status} />
              {check.score != null ? (
                <p className="text-sm text-slate-600">Score: {check.score}</p>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Evidence summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-700">
            <p>
              Subject: {subject.full_name || "Unknown"}{" "}
              {subject.email ? `(${subject.email})` : ""}
            </p>
            <p>External reference: {item.external_reference || "None"}</p>
            <p>Created: {new Date(item.created_at).toLocaleString()}</p>
            <p>Expires: {new Date(item.expires_at).toLocaleString()}</p>
            {item.risk_assessment ? (
              <p>
                Risk: {item.risk_assessment.risk_level} (
                {item.risk_assessment.risk_score}) ·{" "}
                {item.risk_assessment.recommendation}
              </p>
            ) : (
              <p>Risk: Not assessed yet</p>
            )}
            {item.decision ? (
              <p>
                Decision: {item.decision.decision} ·{" "}
                {item.decision.reason_detail}
              </p>
            ) : (
              <p>Decision: Pending</p>
            )}
            {item.evidence_report ? (
              <div className="flex flex-wrap gap-2 pt-2">
                <Button
                  variant="outline"
                  className="rounded-xl"
                  disabled={!!busy}
                  onClick={() => downloadEvidence("json")}
                >
                  <Download className="h-4 w-4" />
                  Evidence JSON
                </Button>
                <Button
                  variant="outline"
                  className="rounded-xl"
                  disabled={!!busy}
                  onClick={() => downloadEvidence("pdf")}
                >
                  <Download className="h-4 w-4" />
                  Evidence PDF
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              onClick={resend}
              disabled={Boolean(busy)}
              className="w-full rounded-xl"
            >
              {busy === "resend" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              Resend fresh link
            </Button>
            <Button
              variant="outline"
              onClick={cancel}
              disabled={Boolean(busy)}
              className="w-full rounded-xl"
            >
              {busy === "cancel" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Cancel request
            </Button>
          </CardContent>
        </Card>
      </div>

      {review && <AuthenticityEvidence verificationId={id} />}

      {review &&
      item.decision?.approval_status === "pending" &&
      !item.decision.can_approve ? (
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Awaiting independent review</CardTitle>
          </CardHeader>
          <CardContent>
            The proposed outcome is{" "}
            <strong>{item.decision.proposed_decision}</strong>. An eligible
            independent reviewer must record the final decision.
          </CardContent>
        </Card>
      ) : null}

      {review &&
      item.status === "manual_review_required" &&
      (!item.decision ||
        ["automatic", "system"].includes(item.decision.decision_type) ||
        (item.decision.approval_status === "pending" &&
          item.decision.can_approve)) ? (
        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>
              {item.decision?.approval_status === "pending"
                ? "Independent approval"
                : "Manual decision"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {item.decision?.approval_status === "pending" ? (
              <p className="text-sm text-slate-600">
                The first reviewer proposed{" "}
                <strong>{item.decision.proposed_decision}</strong>. Confirm the
                final outcome below; your decision is recorded separately from
                the proposal.
              </p>
            ) : null}
            {codes.length ? (
              <div>
                <Label htmlFor="decision_code">Reason code</Label>
                <select
                  id="decision_code"
                  className="w-full rounded-lg border p-2"
                  value={reasonCode}
                  onChange={(event) => setReasonCode(event.target.value)}
                >
                  <option value="">Choose a reason</option>
                  {codes.map((code) => (
                    <option key={code} value={code}>
                      {code}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            <div>
              <Label htmlFor="decision_reason">Reviewer notes</Label>
              <Input
                id="decision_reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                maxLength={4000}
                placeholder="Explain the review decision"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => decide("verified")}
                disabled={Boolean(busy)}
                className="rounded-xl"
              >
                Approve
              </Button>
              <Button
                variant="outline"
                onClick={() => decide("rejected")}
                disabled={Boolean(busy)}
                className="rounded-xl"
              >
                Reject
              </Button>
              <Button
                variant="outline"
                onClick={() => decide("failed")}
                disabled={Boolean(busy)}
                className="rounded-xl"
              >
                Mark failed
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
