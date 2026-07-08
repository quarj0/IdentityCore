import { Button } from "@identitycore/ui";

interface StepActionsProps {
  nextLabel?: string;
  backLabel?: string;
  onNext?: () => void;
  onBack?: () => void;
  nextDisabled?: boolean;
}

export function StepActions({
  nextLabel = "Continue",
  backLabel = "Back",
  onNext,
  onBack,
  nextDisabled,
}: StepActionsProps) {
  return (
    <div className="sticky bottom-0 -mx-5 mt-8 border-t border-slate-200 bg-white/95 px-5 py-4 backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:px-0 sm:py-0">
      <div className="grid gap-3 sm:flex sm:flex-row-reverse sm:justify-end">
        {onNext ? (
          <Button
            type="button"
            onClick={onNext}
            disabled={nextDisabled}
            size="lg"
            className="rounded-xl"
          >
            {nextLabel}
          </Button>
        ) : null}

        {onBack ? (
          <Button
            type="button"
            onClick={onBack}
            variant="outline"
            size="lg"
            className="rounded-xl"
          >
            {backLabel}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
