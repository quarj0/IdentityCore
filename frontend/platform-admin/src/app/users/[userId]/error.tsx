"use client";

import { ErrorState } from "@/components/feedback/error-state";

type UserDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function UserDetailError({
  error,
  reset,
}: UserDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load admin user"
      description={
        error.message || "Something went wrong while loading this admin user."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
