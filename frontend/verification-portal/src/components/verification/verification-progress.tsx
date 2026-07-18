import { Check, Circle } from "lucide-react";

const STEPS = [
  { key: "consent", label: "Consent", description: "Review how your data is used" },
  { key: "document_capture", label: "Identity document", description: "Capture a clear document image" },
  { key: "selfie_capture", label: "Live selfie", description: "Confirm the document belongs to you" },
  { key: "liveness_check", label: "Presence check", description: "Complete passive liveness" },
  { key: "processing", label: "Decision", description: "Secure evidence evaluation" },
] as const;

const STEP_INDEX: Record<string, number> = {
  consent: 0,
  document_capture: 1,
  document_processing: 1,
  selfie_capture: 2,
  liveness_check: 3,
  processing: 4,
  completed: 5,
  failed: 5,
  expired: 5,
  cancelled: 5,
};

export function VerificationProgress({ currentStep }: { currentStep: string }) {
  const currentIndex = STEP_INDEX[currentStep] ?? 0;

  return (
    <nav
      aria-label="Verification progress"
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50"
    >
      <ol className="space-y-1">
        {STEPS.map((step, index) => {
          const complete = index < currentIndex;
          const active = index === currentIndex;
          return (
            <li key={step.key} className="relative flex gap-3 pb-4 last:pb-0">
              {index < STEPS.length - 1 ? (
                <span
                  className={`absolute left-[0.6875rem] top-6 h-[calc(100%-0.5rem)] w-px ${
                    complete ? "bg-blue-500" : "bg-slate-200"
                  }`}
                  aria-hidden="true"
                />
              ) : null}
              <span
                className={`relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${
                  complete
                    ? "border-blue-600 bg-blue-600 text-white"
                    : active
                      ? "border-blue-600 bg-blue-50 text-blue-700 ring-4 ring-blue-50"
                      : "border-slate-300 bg-white text-slate-300"
                }`}
                aria-hidden="true"
              >
                {complete ? <Check className="h-3.5 w-3.5" /> : <Circle className="h-2.5 w-2.5 fill-current" />}
              </span>
              <div>
                <p className={`text-sm font-medium ${active ? "text-blue-700" : complete ? "text-slate-800" : "text-slate-400"}`}>
                  {step.label}
                  {active ? <span className="sr-only">, current step</span> : null}
                  {complete ? <span className="sr-only">, completed</span> : null}
                </p>
                <p className="mt-0.5 text-xs leading-5 text-slate-400">{step.description}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
