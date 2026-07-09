"use client";

import { ErrorState } from "@/components/feedback/error-state";

type TemplateDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function TemplateDetailError({
  error,
  reset,
}: TemplateDetailErrorProps) {
  return (
    <ErrorState
      title="Unable to load template"
      description={error.message || "Something went wrong while loading this template."}
      actionLabel="Try again"
      onAction={reset}
    />
  );
}