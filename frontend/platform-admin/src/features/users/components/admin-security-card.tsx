import type { AdminUser } from "@/features/users/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type AdminSecurityCardProps = {
  user: AdminUser;
};

export function AdminSecurityCard({ user }: AdminSecurityCardProps) {
  const items = [
    {
      label: "Multi-factor authentication",
      value: user.mfaEnabled ? "Enabled" : "Missing",
      good: user.mfaEnabled,
    },
    {
      label: "Single sign-on",
      value: user.ssoEnabled ? "Enabled" : "Not configured",
      good: user.ssoEnabled,
    },
    {
      label: "Risk level",
      value: user.riskLevel,
      good: user.riskLevel === "Low",
    },
    {
      label: "Session count",
      value: `${user.activeSessions} active`,
      good: user.activeSessions <= 3,
    },
  ];

  return (
    <SectionCard
      title="Security"
      description="Authentication, MFA, SSO and access risk posture."
    >
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">{item.label}</p>
              <p className="mt-1 text-xs text-slate-500">{item.value}</p>
            </div>

            <span
              className={
                item.good
                  ? "rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100"
                  : "rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
              }
            >
              {item.good ? "Healthy" : "Review"}
            </span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
