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
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
            {value}
          </p>
        </div>

        <div className="flex size-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Icon className="size-5" aria-hidden="true" />
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
            trend === "up" &&
              "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100",
            trend === "down" && "bg-red-50 text-red-700 ring-1 ring-red-100",
            trend === "neutral" &&
              "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
          )}
        >
          {trend !== "neutral" ? (
            <TrendIcon className="size-3.5" aria-hidden="true" />
          ) : null}
          {change}
        </span>

        {helperText ? (
          <span className="text-xs text-slate-400">{helperText}</span>
        ) : null}
      </div>
    </article>
  );
}
