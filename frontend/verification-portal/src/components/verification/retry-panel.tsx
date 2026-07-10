import { RotateCcw } from "lucide-react";
import { Button } from "@identitycore/ui";

interface RetryPanelProps {
  title: string;
  description: string;
  onRetry: () => void;
  onContinue: () => void;
}

export function RetryPanel({
  title,
  description,
  onRetry,
  onContinue,
}: RetryPanelProps) {
  return (
    <div className="rounded-4xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Button
          type="button"
          variant="outline"
          onClick={onRetry}
          className="rounded-xl"
        >
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          Retry
        </Button>

        <Button type="button" onClick={onContinue} className="rounded-xl">
          Continue with mock evidence
        </Button>
      </div>
    </div>
  );
}
