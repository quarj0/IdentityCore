import { SectionCard } from "@/components/shared/section-card";
import { aiProviderHealthEvents } from "@/features/ai-providers/mock-data";

function getToneClass(severity: string) {
  if (severity === "Success") return "bg-emerald-50 text-emerald-700 ring-emerald-100";
  if (severity === "Warning") return "bg-amber-50 text-amber-700 ring-amber-100";
  return "bg-blue-50 text-blue-700 ring-blue-100";
}

export function AiProviderHealthCard() {
  return (
    <SectionCard
      title="Health events"
      description="Recent provider diagnostics, alerts and operational events."
    >
      <div className="space-y-3">
        {aiProviderHealthEvents.map((event) => (
          <div key={event.title} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-950">{event.title}</p>
                <p className="mt-1 text-xs text-slate-500">{event.provider}</p>
              </div>

              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${getToneClass(event.severity)}`}>
                  {event.severity}
                </span>
                <span className="text-xs text-slate-500">{event.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}