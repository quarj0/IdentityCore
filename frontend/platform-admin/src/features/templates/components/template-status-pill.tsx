import { StatusPill } from "@/components/shared/status-pill";
import type { TemplateRecord } from "@/features/templates/live-data";

type TemplateStatusPillProps = {
  status: TemplateRecord["status"];
};

const labels: Record<string, string> = {
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
