"use client";

import { ErrorState } from "@/components/feedback/error-state";

type OrganizationsErrorProps = {
  error: Error;
  reset: () => void;
};

export default function OrganizationsError({
  error,
  reset,
}: OrganizationsErrorProps) {
  return (
    <ErrorState
      title="Unable to load organizations"
      description={
        error.message || "Something went wrong while loading organizations."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
