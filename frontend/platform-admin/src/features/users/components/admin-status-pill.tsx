import type { AdminStatus } from "@/features/users/mock-data";
import { StatusPill } from "@/components/shared/status-pill";

type AdminStatusPillProps = {
  status: AdminStatus;
};

const labels: Record<AdminStatus, string> = {
  active: "Active",
  invited: "Invited",
  disabled: "Disabled",
  locked: "Locked",
};

export function AdminStatusPill({ status }: AdminStatusPillProps) {
  if (status === "active") {
    return <StatusPill tone="success">{labels[status]}</StatusPill>;
  }

  if (status === "invited") {
    return <StatusPill tone="warning">{labels[status]}</StatusPill>;
  }

  return <StatusPill tone="danger">{labels[status]}</StatusPill>;
}
