"use client";

import { ErrorState } from "@/components/feedback/error-state";

type UsersErrorProps = {
  error: Error;
  reset: () => void;
};

export default function UsersError({ error, reset }: UsersErrorProps) {
  return (
    <ErrorState
      title="Unable to load platform admins"
      description={error.message || "Something went wrong while loading users."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
