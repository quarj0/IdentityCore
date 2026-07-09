"use client";

import { ErrorState } from "@/components/feedback/error-state";

type WorkflowDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function WorkflowDetailError({
  error,
  reset,
}: WorkflowDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load workflow"
      description={error.message || "Something went wrong while loading this workflow."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}