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
        tone === "success" &&
          "bg-emerald-400/10 text-emerald-300 ring-emerald-300/20",
        tone === "warning" &&
          "bg-amber-400/10 text-amber-300 ring-amber-300/20",
        tone === "danger" && "bg-rose-400/10 text-rose-300 ring-rose-300/20",
        tone === "info" && "bg-cyan-400/10 text-cyan-300 ring-cyan-300/20",
        tone === "neutral" && "bg-white/5 text-slate-300 ring-white/10",
      )}
    >
      {children}
    </span>
  );
}
