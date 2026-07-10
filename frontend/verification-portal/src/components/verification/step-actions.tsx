import { ArrowLeft, ArrowRight } from "lucide-react";

interface StepActionsProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  backLabel?: string;
  nextDisabled?: boolean;
}

export function StepActions({
  onBack,
  onNext,
  nextLabel = "Continue",
  backLabel = "Back",
  nextDisabled = false,
}: StepActionsProps) {
  return (
    <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          {backLabel}
        </button>
      ) : (
        <span />
      )}

      {onNext ? (
        <button
          type="button"
          onClick={onNext}
          disabled={nextDisabled}
          className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {nextLabel}
          <ArrowRight className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  );
}
