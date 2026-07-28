"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchCurrentOnboarding } from "@/lib/onboarding-api";
import { getOnboardingRoute } from "@/lib/onboarding-state";
import {
  getOnboardingStepIndex,
  onboardingStepPaths,
} from "@/components/onboarding/onboarding-steps";

export function OnboardingAccessGuard({ pathname }: { pathname: string }) {
  const router = useRouter();

  useEffect(() => {
    let active = true;
    void fetchCurrentOnboarding()
      .then((state) => {
        if (!active || state.currentStep === "active") return;
        const canonicalRoute = getOnboardingRoute(state);
        const requestedIndex = getOnboardingStepIndex(pathname);
        const allowedIndex = getOnboardingStepIndex(canonicalRoute);
        if (requestedIndex > allowedIndex && allowedIndex >= 0) {
          router.replace(onboardingStepPaths[allowedIndex]);
        }
      })
      .catch(() => {
        // The API client handles expired sessions globally. Page-level content owns
        // other recoverable loading errors so this guard never creates a redirect loop.
      });
    return () => {
      active = false;
    };
  }, [pathname, router]);

  return null;
}
