"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ProviderDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ProviderDetailError({
  error,
  reset,
}: ProviderDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load verification provider"
      description={error.message || "Something went wrong while loading this provider."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}