"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  FileText,
  RefreshCcw,
  ShieldCheck,
} from "lucide-react";
import { Button, Textarea } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import {
  fetchOrganizationReview,
  reviewOrganization,
  type OrganizationReviewItem,
} from "@/features/review/review-api";

type ReviewCaseDetailPageProps = {
  caseId: string;
};

function formatDateTime(value: string | null) {
  if (!value) return "Pending";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function reviewStatusTone(status: string) {
  if (status === "approved") return "success";
  if (status === "needs_information") return "warning";
  if (status === "rejected") return "danger";
  if (status === "changed_after_approval") return "info";
  return "neutral";
}

function statusLabel(status: string) {
  return status.replace(/_/g, " ");
}

function asString(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function normalizeSupportingDocuments(
  documents: OrganizationReviewItem["supportingDocuments"],
) {
  return (documents ?? []).map((document, index) => {
    if (typeof document === "string") {
      return {
        id: document || `document-${index}`,
        filename: document || `Document ${index + 1}`,
        status: "uploaded",
        file_size_bytes: undefined,
        download_url: "",
      };
    }

    return {
      id: asString(document.id) || `document-${index}`,
      filename: asString(document.filename) || `Document ${index + 1}`,
      status: asString(document.status) || "uploaded",
      file_size_bytes:
        typeof document.file_size_bytes === "number"
          ? document.file_size_bytes
          : undefined,
      download_url: asString(document.download_url),
    };
  });
}

export function ReviewCaseDetailPage({ caseId }: ReviewCaseDetailPageProps) {
  const [item, setItem] = useState<OrganizationReviewItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingDecision, setSavingDecision] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadReview() {
      setLoading(true);
      setError(null);

      try {
        const review = await fetchOrganizationReview(caseId);
        if (!active) return;
        setItem(review);
        setNote(review?.organizationVerificationReviewNote ?? "");
      } catch (loadError) {
        if (!active) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load the organization review.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadReview();
    return () => {
      active = false;
    };
  }, [caseId, refreshTick]);

  const reviewPillTone = useMemo(
    () => reviewStatusTone(item?.organizationVerificationReviewStatus ?? ""),
    [item],
  );

  async function submitDecision(
    decision: "approved" | "rejected" | "needs_information",
  ) {
    if (!item || savingDecision) return;
    if (!note.trim()) {
      setError("Enter a review rationale before submitting a decision.");
      return;
    }
    if (!window.confirm(`Confirm ${decision.replace(/_/g, " ")} for ${item.organizationName}?`)) {
      return;
    }

    setSavingDecision(decision);
    setError(null);

    try {
      await reviewOrganization(item.organizationId, decision, note);
      const updated = await fetchOrganizationReview(item.organizationId);
      setItem(updated);
      setNote(updated?.organizationVerificationReviewNote ?? note);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to submit review decision.",
      );
    } finally {
      setSavingDecision(null);
      setRefreshTick((value) => value + 1);
    }
  }

  if (loading && !item) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Platform admin review"
          title="Loading organization review"
          description="Fetching the latest review evidence from the backend."
        />
      </div>
    );
  }

  if (error && !item) {
    return (
      <EmptyState
        title="Review item unavailable"
        description={error}
        action={
          <Button onClick={() => setRefreshTick((value) => value + 1)}>
            Try again
          </Button>
        }
      />
    );
  }

  if (!item) {
    return (
      <EmptyState
        title="Review item not found"
        description="This organization review may have already been completed or removed from the queue."
      />
    );
  }

  const supportingDocuments = normalizeSupportingDocuments(item.supportingDocuments);
  const canAct = [
    "submitted",
    "changed_after_approval",
  ].includes(item.organizationVerificationReviewStatus);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link
          href="/review"
          className="inline-flex items-center gap-1 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <ArrowLeft className="size-4" />
          Organization review
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-slate-700">{item.organizationName}</span>
      </nav>

      <PageHeader
        eyebrow="Platform admin review"
        title={item.organizationName}
        description={`${item.organizationCountryName} · ${item.organizationType} · ${item.organizationSlug}`}
        actions={
          <Button
            variant="outline"
            onClick={() => setRefreshTick((value) => value + 1)}
            disabled={loading}
          >
            <RefreshCcw className="mr-2 size-4" />
            Refresh
          </Button>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Review status</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatusPill tone={reviewPillTone}>
              {statusLabel(item.organizationVerificationReviewStatus)}
            </StatusPill>
            {item.organizationVerificationChangedAfterApproval ? (
              <StatusPill tone="info">changed after approval</StatusPill>
            ) : null}
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Organization</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{item.organizationStatus}</p>
          <p className="mt-1 text-sm text-slate-500">Tenant: {item.tenantStatus}</p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Submitted</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {formatDateTime(item.organizationVerificationSubmittedAt)}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Reviewed: {formatDateTime(item.organizationVerificationReviewedAt)}
          </p>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Priority</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {item.reviewPriority ?? "normal"}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {item.reviewSummary ?? "Backend-generated review summary"}
          </p>
        </div>
      </section>

      {error ? (
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <SectionCard
            title="Submitted evidence"
            description="Organization details and uploaded supporting documents sent by the tenant."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Business registration number
                </p>
                <p className="mt-2 text-sm font-medium text-slate-950">
                  {item.businessRegistrationNumber || "Not provided"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Tax identification number
                </p>
                <p className="mt-2 text-sm font-medium text-slate-950">
                  {item.taxIdentificationNumber || "Not provided"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:col-span-2">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Registered address
                </p>
                <p className="mt-2 text-sm font-medium leading-6 text-slate-950">
                  {item.registeredAddress || "Not provided"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:col-span-2">
                <p className="text-xs uppercase tracking-wide text-slate-500">Official website</p>
                <p className="mt-2 text-sm font-medium text-slate-950">
                  {item.officialWebsite || item.website || "Not provided"}
                </p>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {supportingDocuments.length > 0 ? (
                supportingDocuments.map((document) => (
                  <div
                    key={document.id}
                    className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl bg-blue-50 p-2 text-blue-700">
                        <FileText className="size-5" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-950">{document.filename}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {document.status}
                          {document.file_size_bytes ? ` · ${document.file_size_bytes} bytes` : ""}
                        </p>
                      </div>
                    </div>

                    {document.download_url ? (
                      <Button asChild variant="outline" size="sm">
                        <a href={document.download_url} target="_blank" rel="noreferrer">
                          Open file
                        </a>
                      </Button>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                  No supporting documents were attached to this submission.
                </div>
              )}
            </div>
          </SectionCard>

          <SectionCard
            title="Review note"
            description="Record the reason for the decision and guide the tenant if more information is needed."
          >
            <Textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Add a reviewer note..."
              className="min-h-35"
              disabled={!canAct || savingDecision !== null}
            />

            {canAct ? (
            <div className="mt-4 flex flex-wrap gap-2">
              <Button
                onClick={() => submitDecision("approved")}
                disabled={savingDecision !== null}
              >
                <ShieldCheck className="mr-2 size-4" />
                {savingDecision === "approved" ? "Approving..." : "Approve"}
              </Button>
              <Button
                variant="outline"
                onClick={() => submitDecision("needs_information")}
                disabled={savingDecision !== null}
              >
                {savingDecision === "needs_information"
                  ? "Requesting..."
                  : "Request more information"}
              </Button>
              <Button
                variant="destructive"
                onClick={() => submitDecision("rejected")}
                disabled={savingDecision !== null}
              >
                <AlertTriangle className="mr-2 size-4" />
                {savingDecision === "rejected" ? "Rejecting..." : "Reject"}
              </Button>
            </div>
            ) : (
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                This review is closed. The recorded decision is immutable until the organization submits new evidence.
              </div>
            )}
          </SectionCard>
        </div>

        <div className="space-y-4">
          <SectionCard
            title="Submission metadata"
            description="State returned by the backend review workflow."
          >
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Current step</dt>
                <dd className="mt-1 font-medium text-slate-950">{item.currentStep}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Editable</dt>
                <dd className="mt-1 font-medium text-slate-950">
                  {item.organizationVerificationEditable ? "Yes" : "Locked"}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Platform review</dt>
                <dd className="mt-1 font-medium text-slate-950">
                  {statusLabel(item.platformReviewStatus)}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Platform review note</dt>
                <dd className="mt-1 leading-6 text-slate-700">
                  {item.platformReviewNote || "No platform review note recorded yet."}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Platform reviewed at</dt>
                <dd className="mt-1 font-medium text-slate-950">
                  {formatDateTime(item.platformReviewedAt)}
                </dd>
              </div>
            </dl>
          </SectionCard>

          <SectionCard
            title="Administrator identity"
            description="Identity verification submitted as part of organization onboarding."
          >
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Verification status</dt>
                <dd className="mt-1">
                  <StatusPill tone={reviewStatusTone(item.administratorIdentityVerificationStatus)}>
                    {statusLabel(item.administratorIdentityVerificationStatus || "pending")}
                  </StatusPill>
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Verification ID</dt>
                <dd className="mt-1 break-all font-mono text-xs text-slate-800">
                  {item.administratorIdentityVerificationId || "Not submitted"}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Submitted</dt>
                <dd className="mt-1 font-medium text-slate-950">
                  {formatDateTime(item.administratorIdentitySubmittedAt)}
                </dd>
              </div>
            </dl>
          </SectionCard>

          <SectionCard
            title="Risk cues"
            description="Signals that help reviewers understand why this record is on the queue."
          >
            <div className="space-y-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="flex items-center gap-2 text-sm font-medium text-slate-950">
                  <ShieldCheck className="size-4 text-blue-600" />
                  Review state
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  {item.reviewSummary ??
                    "The backend has flagged this organization for human review."}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="flex items-center gap-2 text-sm font-medium text-slate-950">
                  <AlertTriangle className="size-4 text-amber-600" />
                  Changed after approval
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  {item.organizationVerificationChangedAfterApproval
                    ? "This submission was edited after a previous approval and has been returned to review."
                    : "This submission has not been edited after approval."}
                </p>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
