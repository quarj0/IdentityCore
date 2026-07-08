import { CheckCircle2, RotateCcw } from "lucide-react";
import { CapturePanel } from "./capture-panel";
import { StepActions } from "./step-actions";

interface CaptureReviewStepProps {
  title: string;
  description: string;
  items: string[];
  onNext: () => void;
  onBack: () => void;
  onRetry: () => void;
}

export function CaptureReviewStep({
  title,
  description,
  items,
  onNext,
  onBack,
  onRetry,
}: CaptureReviewStepProps) {
  return (
    <CapturePanel title={title} description={description}>
      <div className="rounded-[2rem] border border-slate-200 bg-slate-50 p-5">
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item} className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium">{item}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-950"
        >
          <RotateCcw className="h-4 w-4" />
          Retake capture
        </button>
      </div>

      <StepActions onBack={onBack} onNext={onNext} nextLabel="Looks good" />
    </CapturePanel>
  );
}
