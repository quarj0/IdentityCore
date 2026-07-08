import { useState } from "react";
import { documentTypes } from "@/data/verification";
import { CapturePanel } from "./capture-panel";
import { StepActions } from "./step-actions";

interface DocumentTypeStepProps {
  onNext: (documentType: string) => void;
  onBack: () => void;
}

export function DocumentTypeStep({ onNext, onBack }: DocumentTypeStepProps) {
  const [selected, setSelected] = useState(documentTypes[0]);

  return (
    <CapturePanel
      title="Choose document type"
      description="Select the identity document you want to use for this verification."
    >
      <div className="grid gap-3 sm:grid-cols-2">
        {documentTypes.map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => setSelected(type)}
            className={
              selected === type
                ? "rounded-2xl border border-blue-200 bg-blue-50 p-5 text-left text-sm font-semibold text-blue-700"
                : "rounded-2xl border border-slate-200 bg-white p-5 text-left text-sm font-semibold text-slate-700 hover:bg-slate-50"
            }
          >
            {type}
          </button>
        ))}
      </div>

      <StepActions
        onBack={onBack}
        onNext={() => onNext(selected)}
        nextLabel="Continue"
      />
    </CapturePanel>
  );
}
