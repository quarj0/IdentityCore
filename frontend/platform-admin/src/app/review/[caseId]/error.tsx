"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ReviewCaseErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ReviewCaseError({ error, reset }: ReviewCaseErrorProps) {
  return (
    <ErrorState
      title="Unable to load review case"
      description={error.message || "Something went wrong while loading this review case."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}