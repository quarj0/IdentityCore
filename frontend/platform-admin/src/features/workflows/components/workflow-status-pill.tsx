import { StatusPill } from "@/components/shared/status-pill";
import type { WorkflowRecord } from "@/features/workflows/live-data";

type WorkflowStatusPillProps = {
  status: WorkflowRecord["status"];
};

const labels: Record<string, string> = {
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
