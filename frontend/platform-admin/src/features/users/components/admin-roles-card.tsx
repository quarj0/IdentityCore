import type { AdminUser } from "@/features/users/mock-data";
import { SectionCard } from "@/components/shared/section-card";

type AdminRolesCardProps = {
  user: AdminUser;
};

const roleAccess = [
  "Platform-wide read access",
  "Organization lifecycle management",
  "Tenant visibility",
  "Audit event visibility",
];

export function AdminRolesCard({ user }: AdminRolesCardProps) {
  return (
    <SectionCard
      title="Role"
      description="Current role assignment and inherited access."
    >
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-500">Assigned role</p>
        <p className="mt-2 text-xl font-semibold text-slate-950">{user.role}</p>
      </div>

      <div className="mt-4 space-y-2">
        {roleAccess.map((item) => (
          <div
            key={item}
            className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm"
          >
            <span className="text-slate-700">{item}</span>
            <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100">
              Granted
            </span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
