import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@identitycore/ui";

type MetricCardProps = {
  label: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  icon: LucideIcon;
  helperText?: string;
};

export function MetricCard({
  label,
  value,
  change,
  trend,
  icon: Icon,
  helperText,
}: MetricCardProps) {
  const TrendIcon = trend === "down" ? ArrowDownRight : ArrowUpRight;

  return (
    <article className="rounded-2xl border border-white/10 bg-white/3 p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-tight text-white">
            {value}
          </p>
        </div>

        <div className="flex size-11 items-center justify-center rounded-2xl bg-white/5 text-cyan-300 ring-1 ring-white/10">
          <Icon className="size-5" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
            trend === "up" && "bg-emerald-400/10 text-emerald-300",
            trend === "down" && "bg-rose-400/10 text-rose-300",
            trend === "neutral" && "bg-slate-400/10 text-slate-300",
          )}
        >
          {trend !== "neutral" ? (
            <TrendIcon className="size-3.5" aria-hidden="true" />
          ) : null}
          {change}
        </span>

        {helperText ? (
          <span className="text-xs text-slate-500">{helperText}</span>
        ) : null}
      </div>
    </article>
  );
}
