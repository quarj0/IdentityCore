import type { OrganizationStatus } from "@/features/organizations/mock-data";
import { StatusPill } from "@/components/shared/status-pill";

type OrganizationStatusPillProps = {
  status: OrganizationStatus;
};

const statusLabel: Record<OrganizationStatus, string> = {
  active: "Active",
  pending_review: "Pending review",
  suspended: "Suspended",
  rejected: "Rejected",
  deleted: "Deleted",
};

export function OrganizationStatusPill({
  status,
}: OrganizationStatusPillProps) {
  if (status === "active") {
    return <StatusPill tone="success">{statusLabel[status]}</StatusPill>;
  }

  if (status === "pending_review") {
    return <StatusPill tone="warning">{statusLabel[status]}</StatusPill>;
  }

  if (status === "suspended" || status === "rejected") {
    return <StatusPill tone="danger">{statusLabel[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{statusLabel[status]}</StatusPill>;
}
