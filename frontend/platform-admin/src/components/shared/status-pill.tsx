import { cn } from "@identitycore/ui";

type StatusPillTone = "success" | "warning" | "danger" | "neutral" | "info";

type StatusPillProps = {
  children: string;
  tone?: StatusPillTone;
};

export function StatusPill({ children, tone = "neutral" }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1",
        tone === "success" && "bg-emerald-50 text-emerald-700 ring-emerald-100",
        tone === "warning" && "bg-amber-50 text-amber-700 ring-amber-100",
        tone === "danger" && "bg-red-50 text-red-700 ring-red-100",
        tone === "info" && "bg-blue-50 text-blue-700 ring-blue-100",
        tone === "neutral" && "bg-slate-100 text-slate-700 ring-slate-200",
      )}
    >
      {children}
    </span>
  );
}
