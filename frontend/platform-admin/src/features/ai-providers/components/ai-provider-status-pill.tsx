import { StatusPill } from "@/components/shared/status-pill";
import type { AiProviderStatus } from "@/features/ai-providers/mock-data";

type AiProviderStatusPillProps = {
  status: AiProviderStatus;
};

const labels: Record<AiProviderStatus, string> = {
  operational: "Operational",
  degraded: "Degraded",
  disabled: "Disabled",
  testing: "Testing",
};

export function AiProviderStatusPill({ status }: AiProviderStatusPillProps) {
  if (status === "operational") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "degraded" || status === "testing") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{labels[status]}</StatusPill>;
}