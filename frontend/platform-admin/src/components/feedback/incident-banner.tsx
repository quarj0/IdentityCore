import { AlertTriangle } from "lucide-react";
import { Button } from "@identitycore/ui";

type IncidentBannerProps = {
  title: string;
  description: string;
  severity: "minor" | "major" | "critical";
};

export function IncidentBanner({
  title,
  description,
  severity,
}: IncidentBannerProps) {
  const label = {
    minor: "Minor incident",
    major: "Major incident",
    critical: "Critical incident",
  }[severity];

  return (
    <div className="rounded-2xl border border-accent bg-amber-50 p-4 text-slate-950">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <AlertTriangle
            className="mt-0.5 size-5 shrink-0 text-amber-500"
            aria-hidden="true"
          />

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
              {label}
            </p>
            <h2 className="mt-1 text-sm font-semibold text-slate-950">
              {title}
            </h2>
            <p className="mt-1 text-sm leading-6 text-slate-700">
              {description}
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          className="border-amber-300 bg-white text-slate-950 hover:bg-amber-100"
        >
          View incident
        </Button>
      </div>
    </div>
  );
}
