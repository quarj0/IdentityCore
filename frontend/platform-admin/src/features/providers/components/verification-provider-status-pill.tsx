import { StatusPill } from "@/components/shared/status-pill";
import type { VerificationProviderStatus } from "@/features/providers/mock-data";

type VerificationProviderStatusPillProps = {
  status: VerificationProviderStatus;
};

const labels: Record<VerificationProviderStatus, string> = {
  planned: "Planned",
  sandbox: "Sandbox",
  active: "Active",
  disabled: "Disabled",
  deprecated: "Deprecated",
};

export function VerificationProviderStatusPill({
  status,
}: VerificationProviderStatusPillProps) {
  if (status === "active") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "sandbox" || status === "planned") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="neutral">{labels[status]}</StatusPill>;
}