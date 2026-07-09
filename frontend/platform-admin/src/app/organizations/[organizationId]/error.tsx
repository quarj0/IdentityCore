"use client";

import { ErrorState } from "@/components/feedback/error-state";

type OrganizationDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function OrganizationDetailError({
  error,
  reset,
}: OrganizationDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load organization"
      description={
        error.message || "Something went wrong while loading this organization."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
