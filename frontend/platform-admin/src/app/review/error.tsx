"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ReviewErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ReviewError({ error, reset }: ReviewErrorProps) {
  return (
    <ErrorState
      title="Unable to load review queue"
      description={error.message || "Something went wrong while loading manual review cases."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}