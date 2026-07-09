import { StatusPill } from "@/components/shared/status-pill";
import type { TenantStatus } from "@/features/tenants/mock-data";

type TenantStatusPillProps = {
  status: TenantStatus;
};

const statusLabel: Record<TenantStatus, string> = {
  healthy: "Healthy",
  degraded: "Degraded",
  maintenance: "Maintenance",
  provisioning: "Provisioning",
  offline: "Offline",
};

export function TenantStatusPill({ status }: TenantStatusPillProps) {
  if (status === "healthy") {
    return <StatusPill tone="success">{statusLabel[status]}</StatusPill>;
  }

  if (
    status === "degraded" ||
    status === "maintenance" ||
    status === "provisioning"
  ) {
    return <StatusPill tone="warning">{statusLabel[status]}</StatusPill>;
  }

  return <StatusPill tone="danger">{statusLabel[status]}</StatusPill>;
}
