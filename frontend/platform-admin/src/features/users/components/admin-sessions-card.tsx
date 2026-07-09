import { Button } from "@identitycore/ui";
import { SectionCard } from "@/components/shared/section-card";
import { adminSessions } from "@/features/users/mock-data";

export function AdminSessionsCard() {
  return (
    <SectionCard
      title="Sessions"
      description="Current and recent platform admin sessions."
      action={<Button variant="outline">Revoke all</Button>}
    >
      <div className="space-y-3">
        {adminSessions.map((session) => (
          <div
            key={session.id}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="text-sm font-medium text-slate-950">
                {session.device}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {session.location} · {session.ipAddress}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
                {session.status}
              </span>
              <span className="text-xs text-slate-500">{session.lastSeen}</span>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
