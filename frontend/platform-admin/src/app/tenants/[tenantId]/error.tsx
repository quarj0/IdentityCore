"use client";

import { ErrorState } from "@/components/feedback/error-state";

type TenantDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function TenantDetailError({
  error,
  reset,
}: TenantDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load tenant"
      description={
        error.message || "Something went wrong while loading this tenant."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
