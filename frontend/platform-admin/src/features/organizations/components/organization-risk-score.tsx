import type { OrganizationRiskLevel } from "@/features/organizations/mock-data";
import { cn } from "@identitycore/ui";

type OrganizationRiskScoreProps = {
  score: number;
  level: OrganizationRiskLevel;
};

const riskLabel: Record<OrganizationRiskLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

export function OrganizationRiskScore({
  score,
  level,
}: OrganizationRiskScoreProps) {
  return (
    <div className="flex items-center gap-3">
      <div
        className="h-2 w-24 overflow-hidden rounded-full bg-white/10"
        aria-hidden="true"
      >
        <div
          className={cn(
            "h-full rounded-full",
            level === "low" && "bg-emerald-300",
            level === "medium" && "bg-amber-300",
            level === "high" && "bg-orange-300",
            level === "critical" && "bg-rose-300",
          )}
          style={{ width: `${score}%` }}
        />
      </div>

      <span
        className={cn(
          "text-xs font-medium",
          level === "low" && "text-emerald-300",
          level === "medium" && "text-amber-300",
          level === "high" && "text-orange-300",
          level === "critical" && "text-rose-300",
        )}
      >
        {riskLabel[level]} · {score}
      </span>
    </div>
  );
}
