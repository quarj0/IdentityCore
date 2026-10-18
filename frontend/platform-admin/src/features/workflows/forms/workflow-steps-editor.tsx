"use client";

import { Button } from "@identitycore/ui";

export const workflowStepLabels = {
  consent: "Consent",
  document: "Identity document",
  selfie: "Selfie",
  liveness: "Liveness",
  face_match: "Face match",
  decision: "Decision",
  manual_review: "Manual review",
  webhook: "Webhook",
} as const;
export type WorkflowStep = keyof typeof workflowStepLabels;
export const defaultWorkflowSteps: WorkflowStep[] = [
  "consent",
  "document",
  "decision",
];

export function isWorkflowStep(value: unknown): value is WorkflowStep {
  return typeof value === "string" && Object.hasOwn(workflowStepLabels, value);
}

export function WorkflowStepsEditor({
  steps,
  onChange,
}: {
  steps: WorkflowStep[];
  onChange: (steps: WorkflowStep[]) => void;
}) {
  function move(index: number, offset: number) {
    const next = [...steps];
    [next[index], next[index + offset]] = [next[index + offset], next[index]];
    onChange(next);
  }
  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-medium">Workflow steps</legend>
      <p className="text-sm text-slate-600">
        Choose the sequence to publish. Consent and decision are required.
      </p>
      <ol className="space-y-2">
        {steps.map((step, index) => (
          <li key={step} className="flex flex-wrap items-center gap-2">
            <span className="mr-auto text-sm">
              {index + 1}. {workflowStepLabels[step]}
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Move ${workflowStepLabels[step]} up`}
              disabled={index === 0}
              onClick={() => move(index, -1)}
            >
              Up
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Move ${workflowStepLabels[step]} down`}
              disabled={index === steps.length - 1}
              onClick={() => move(index, 1)}
            >
              Down
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Remove ${workflowStepLabels[step]}`}
              disabled={step === "consent" || step === "decision"}
              onClick={() => onChange(steps.filter((value) => value !== step))}
            >
              Remove
            </Button>
          </li>
        ))}
      </ol>
      <div className="flex flex-wrap gap-2">
        {(Object.keys(workflowStepLabels) as WorkflowStep[])
          .filter((step) => !steps.includes(step))
          .map((step) => (
            <Button
              key={step}
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                const index = steps.indexOf("decision");
                const next = [...steps];
                next.splice(index < 0 ? next.length : index, 0, step);
                onChange(next);
              }}
            >
              Add {workflowStepLabels[step]}
            </Button>
          ))}
      </div>
    </fieldset>
  );
}
