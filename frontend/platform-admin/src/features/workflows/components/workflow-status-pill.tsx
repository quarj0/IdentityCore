import { StatusPill } from "@/components/shared/status-pill";
import type { WorkflowStatus } from "@/features/workflows/mock-data";

type WorkflowStatusPillProps = {
  status: WorkflowStatus;
};

const labels: Record<WorkflowStatus, string> = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
};

export function WorkflowStatusPill({ status }: WorkflowStatusPillProps) {
  if (status === "published") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "draft") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{labels[status]}</StatusPill>;
}