import { Check, Loader2 } from "lucide-react";
import { Button } from "@identitycore/ui";
import { CapturePanel } from "./capture-panel";

interface ProcessingStepProps {
  onResult: (state: "approved" | "review" | "rejected") => void;
}

export function ProcessingStep({ onResult }: ProcessingStepProps) {
  return (
    <CapturePanel
      title="Processing your verification"
      description="IdentityCore is simulating document analysis, face match, liveness, and policy decisioning."
    >
      <div className="space-y-3">
        {[
          "Reading document fields",
          "Checking document authenticity",
          "Comparing document face with selfie",
          "Evaluating liveness evidence",
          "Applying workflow policy",
        ].map((item) => (
          <div
            key={item}
            className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <Check className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium">{item}</span>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <Button onClick={() => onResult("approved")} className="rounded-xl">
          <Loader2 className="h-4 w-4 animate-spin" />
          Approved
        </Button>

        <Button
          variant="outline"
          onClick={() => onResult("review")}
          className="rounded-xl"
        >
          Needs review
        </Button>

        <Button
          variant="outline"
          onClick={() => onResult("rejected")}
          className="rounded-xl"
        >
          Rejected
        </Button>
      </div>
    </CapturePanel>
  );
}
