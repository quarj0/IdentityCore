"use client";

import { ErrorState } from "@/components/feedback/error-state";

type ErrorProps = {
  error: Error;
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorProps) {
  return (
    <ErrorState
      title="Unable to load page"
      description={error.message || "Something went wrong while loading this page."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}