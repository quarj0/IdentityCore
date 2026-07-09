"use client";

import { ErrorState } from "@/components/feedback/error-state";

type WorkflowsErrorProps = {
  error: Error;
  reset: () => void;
};

export default function WorkflowsError({ error, reset }: WorkflowsErrorProps) {
  return (
    <ErrorState
      title="Unable to load workflows"
      description={error.message || "Something went wrong while loading workflows."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}