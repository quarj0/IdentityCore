import { Check } from "lucide-react";
import { verificationSteps, type VerificationStep } from "@/data/verification";

interface VerificationProgressProps {
  currentStep: VerificationStep;
}

export function VerificationProgress({
  currentStep,
}: VerificationProgressProps) {
  const currentIndex = verificationSteps.findIndex(
    (step) => step.key === currentStep,
  );

  return (
    <nav aria-label="Verification progress" className="overflow-x-auto">
      <ol className="flex min-w-max gap-2">
        {verificationSteps.map((step, index) => {
          const complete = index < currentIndex;
          const active = index === currentIndex;

          return (
            <li
              key={step.key}
              className={
                active
                  ? "flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white"
                  : complete
                    ? "flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700"
                    : "flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-medium text-slate-500 ring-1 ring-slate-200"
              }
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/20 text-xs">
                {complete ? <Check className="h-3 w-3" /> : index + 1}
              </span>
              {step.label}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
