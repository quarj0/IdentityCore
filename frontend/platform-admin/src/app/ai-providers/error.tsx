"use client";

import { ErrorState } from "@/components/feedback/error-state";

type AiProvidersErrorProps = {
  error: Error;
  reset: () => void;
};

export default function AiProvidersError({
  error,
  reset,
}: AiProvidersErrorProps) {
  return (
    <ErrorState
      title="Unable to load AI providers"
      description={error.message || "Something went wrong while loading AI providers."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}