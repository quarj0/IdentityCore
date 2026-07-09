import { StatusPill } from "@/components/shared/status-pill";
import type { TemplateStatus } from "@/features/templates/mock-data";

type TemplateStatusPillProps = {
  status: TemplateStatus;
};

const labels: Record<TemplateStatus, string> = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
};

export function TemplateStatusPill({ status }: TemplateStatusPillProps) {
  if (status === "published") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "draft") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{labels[status]}</StatusPill>;
}