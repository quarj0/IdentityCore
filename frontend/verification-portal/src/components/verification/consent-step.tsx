import { ShieldCheck } from "lucide-react";
import { Checkbox, Label } from "@identitycore/ui";
import { CapturePanel } from "./capture-panel";
import { StepActions } from "./step-actions";

interface ConsentStepProps {
  onNext: () => void;
  onExpire: () => void;
}

export function ConsentStep({ onNext, onExpire }: ConsentStepProps) {
  return (
    <CapturePanel
      title="Consent to identity verification"
      description="Review why your identity is being verified before continuing."
    >
      <div className="space-y-5">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex gap-3">
            <ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-blue-600" />
            <div>
              <p className="text-sm font-medium">What will be processed</p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                <li>Identity document image</li>
                <li>Selfie image</li>
                <li>Liveness evidence</li>
                <li>Verification metadata and audit events</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4">
          <Checkbox id="consent" className="mt-1" />
          <Label htmlFor="consent" className="text-sm leading-6 text-slate-600">
            I consent to this organization using IdentityCore to process my
            identity evidence for this verification workflow.
          </Label>
        </div>

        <div className="flex flex-wrap gap-3">
          <StepActions onNext={onNext} nextLabel="Continue" />
          <button
            type="button"
            onClick={onExpire}
            className="rounded-xl px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-950"
          >
            Simulate expired session
          </button>
        </div>
      </div>
    </CapturePanel>
  );
}
