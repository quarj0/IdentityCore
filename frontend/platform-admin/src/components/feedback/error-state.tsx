import { AlertCircle } from "lucide-react";
import { Button } from "@identitycore/ui";

type ErrorStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function ErrorState({
  title,
  description,
  actionLabel,
  onAction,
}: ErrorStateProps) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-rose-400/10 text-rose-300">
          <AlertCircle className="size-6" aria-hidden="true" />
        </div>

        <h1 className="mt-5 text-lg font-semibold text-white">{title}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>

        {actionLabel && onAction ? (
          <Button onClick={onAction} className="mt-6">
            {actionLabel}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
