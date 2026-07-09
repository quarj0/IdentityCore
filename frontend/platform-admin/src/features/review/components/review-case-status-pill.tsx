import { StatusPill } from "@/components/shared/status-pill";
import type { ReviewCaseStatus } from "@/features/review/mock-data";

type ReviewCaseStatusPillProps = {
  status: ReviewCaseStatus;
};

const labels: Record<ReviewCaseStatus, string> = {
  pending: "Pending",
  assigned: "Assigned",
  escalated: "Escalated",
  approved: "Approved",
  rejected: "Rejected",
};

export function ReviewCaseStatusPill({ status }: ReviewCaseStatusPillProps) {
  if (status === "approved") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "pending" || status === "assigned") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  if (status === "escalated" || status === "rejected") {
    return <StatusPill tone="danger">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{labels[status]}</StatusPill>;
}