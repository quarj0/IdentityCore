"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ProvidersErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ProvidersError({ error, reset }: ProvidersErrorProps) {
  return (
    <ErrorState
      title="Unable to load verification providers"
      description={error.message || "Something went wrong while loading verification providers."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}