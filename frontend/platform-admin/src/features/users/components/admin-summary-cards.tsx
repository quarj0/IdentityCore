import { Fingerprint, KeyRound, ShieldCheck, Users } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import type { AdminUser } from "@/features/users/mock-data";

type AdminSummaryCardsProps = {
  user: AdminUser;
};

export function AdminSummaryCards({ user }: AdminSummaryCardsProps) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        label="Active sessions"
        value={user.activeSessions.toString()}
        change={user.activeSessions > 0 ? "Online" : "No sessions"}
        trend={user.activeSessions > 0 ? "up" : "neutral"}
        helperText="current"
        icon={Users}
      />

      <MetricCard
        label="Permissions"
        value={user.permissionsCount.toString()}
        change={user.role}
        trend="neutral"
        helperText="assigned"
        icon={KeyRound}
      />

      <MetricCard
        label="MFA"
        value={user.mfaEnabled ? "Enabled" : "Missing"}
        change={user.mfaEnabled ? "Protected" : "Action needed"}
        trend={user.mfaEnabled ? "up" : "down"}
        helperText="security"
        icon={Fingerprint}
      />

      <MetricCard
        label="Security risk"
        value={user.riskLevel}
        change={user.ssoEnabled ? "SSO enabled" : "Password login"}
        trend={user.riskLevel === "Low" ? "up" : "down"}
        helperText="access"
        icon={ShieldCheck}
      />
    </section>
  );
}
