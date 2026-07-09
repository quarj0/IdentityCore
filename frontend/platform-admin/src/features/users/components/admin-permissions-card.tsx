import { SectionCard } from "@/components/shared/section-card";
import { adminPermissions } from "@/features/users/mock-data";

export function AdminPermissionsCard() {
  return (
    <SectionCard
      title="Permissions"
      description="Fine-grained permission groups assigned to this admin."
    >
      <div className="space-y-4">
        {adminPermissions.map((group) => (
          <div
            key={group.group}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <h3 className="text-sm font-semibold text-slate-950">
              {group.group}
            </h3>

            <div className="mt-3 flex flex-wrap gap-2">
              {group.permissions.map((permission) => (
                <span
                  key={permission}
                  className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200"
                >
                  {permission}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
