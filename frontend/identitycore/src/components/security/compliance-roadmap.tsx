import { CheckCircle2, CircleDashed } from "lucide-react";

const roadmap = [
  {
    title: "Privacy-first architecture",
    status: "Foundation",
    done: true,
  },
  {
    title: "Audit logs and consent records",
    status: "Foundation",
    done: true,
  },
  {
    title: "Organization approval workflow",
    status: "Version 1",
    done: true,
  },
  {
    title: "Data retention controls",
    status: "Version 1",
    done: false,
  },
  {
    title: "Compliance exports",
    status: "Future",
    done: false,
  },
  {
    title: "Dedicated deployment support",
    status: "Future",
    done: false,
  },
];

export function ComplianceRoadmap() {
  return (
    <div className="grid gap-3">
      {roadmap.map((item) => (
        <div
          key={item.title}
          className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
        >
          {item.done ? (
            <CheckCircle2 className="h-5 w-5 text-blue-300" />
          ) : (
            <CircleDashed className="h-5 w-5 text-slate-400" />
          )}

          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-100">{item.title}</p>
            <p className="mt-1 text-xs text-slate-400">{item.status}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
