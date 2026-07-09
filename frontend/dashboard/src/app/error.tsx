"use client"

import { FeatureErrorState } from "@/components/feedback/feature-error-state";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return <FeatureErrorState reset={reset} />;
}
