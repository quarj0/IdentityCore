import { SectionCard } from "@/components/shared/section-card";
import { adminActivity } from "@/features/users/mock-data";

function getToneClass(severity: string) {
  if (severity === "Success") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-100";
  }

  if (severity === "Warning") {
    return "bg-amber-50 text-amber-700 ring-amber-100";
  }

  return "bg-blue-50 text-blue-700 ring-blue-100";
}

export function AdminActivityCard() {
  return (
    <SectionCard
      title="Recent activity"
      description="Recent actions performed by this platform admin."
    >
      <div className="space-y-3">
        {adminActivity.map((activity) => (
          <div
            key={activity.id}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-950">
                  {activity.action}
                </p>
                <p className="mt-1 text-xs text-slate-500">{activity.target}</p>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${getToneClass(
                    activity.severity,
                  )}`}
                >
                  {activity.severity}
                </span>
                <span className="text-xs text-slate-500">{activity.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
