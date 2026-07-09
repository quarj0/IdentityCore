"use client";

import { ErrorState } from "@/components/feedback/error-state";

type TenantsErrorProps = {
  error: Error;
  reset: () => void;
};

export default function TenantsError({ error, reset }: TenantsErrorProps) {
  return (
    <ErrorState
      title="Unable to load tenants"
      description={
        error.message || "Something went wrong while loading tenants."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
