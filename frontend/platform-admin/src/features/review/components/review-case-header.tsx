import { Button } from "@identitycore/ui";
import type { ReviewCase } from "@/features/review/mock-data";
import { ReviewCaseStatusPill } from "@/features/review/components/review-case-status-pill";
import { ReviewEscalationDialog } from "@/features/review/components/review-escalation-dialog";
import { ReviewerAssignmentDialog } from "@/features/review/components/reviewer-assignment-dialog";

type ReviewCaseHeaderProps = {
  reviewCase: ReviewCase;
};

export function ReviewCaseHeader({ reviewCase }: ReviewCaseHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {reviewCase.applicantName}
            </h1>
            <ReviewCaseStatusPill status={reviewCase.status} />
          </div>

          <p className="mt-2 text-sm text-slate-600">
            {reviewCase.id} · {reviewCase.organizationName} · {reviewCase.documentType}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Country</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{reviewCase.country}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Risk</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{reviewCase.riskScore}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Assigned</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{reviewCase.assignedTo}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">SLA due</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{reviewCase.slaDueAt}</dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <ReviewerAssignmentDialog caseId={reviewCase.id} />
          <ReviewEscalationDialog caseId={reviewCase.id} />
          <Button variant="outline">Reject</Button>
          <Button>Approve</Button>
        </div>
      </div>
    </section>
  );
}