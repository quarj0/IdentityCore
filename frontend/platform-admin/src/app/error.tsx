"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ErrorPageProps = {
  error: Error;
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return (
    <ErrorState
      title="Unable to load platform dashboard"
      description={
        error.message || "Something went wrong while loading this page."
      }
      actionLabel="Try again"
      onAction={reset}
    />
  );
}
