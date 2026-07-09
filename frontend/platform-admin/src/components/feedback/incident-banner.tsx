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
    <div className="rounded-2xl border border-amber-300/20 bg-amber-400/10 p-4 text-amber-100">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <AlertTriangle
            className="mt-0.5 size-5 shrink-0 text-amber-300"
            aria-hidden="true"
          />

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">
              {label}
            </p>
            <h2 className="mt-1 text-sm font-semibold text-amber-50">
              {title}
            </h2>
            <p className="mt-1 text-sm leading-6 text-amber-100/80">
              {description}
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          className="border-amber-300/30 bg-amber-300/10 text-amber-50 hover:bg-amber-300/20"
        >
          View incident
        </Button>
      </div>
    </div>
  );
}
