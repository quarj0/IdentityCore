"use client";

import { ErrorState } from "@/components/feedback/error-state";

type AiProviderDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function AiProviderDetailError({
  error,
  reset,
}: AiProviderDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load AI provider"
      description={error.message || "Something went wrong while loading this AI provider."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}