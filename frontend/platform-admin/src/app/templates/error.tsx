"use client";

import { ErrorState } from "@/components/feedback/error-state";

type TemplatesErrorProps = {
  error: Error;
  reset: () => void;
};

export default function TemplatesError({ error, reset }: TemplatesErrorProps) {
  return (
    <ErrorState
      title="Unable to load templates"
      description={error.message || "Something went wrong while loading templates."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}