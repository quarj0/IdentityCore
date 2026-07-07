export type VerificationStep = "consent" | "document" | "selfie" | "liveness" | "submitting" | "complete";
export type VerificationSessionStatus = "active" | "expired" | "completed" | "error";

export interface VerificationSession {
  sessionId: string;
  organizationName: string;
  purpose: string;
  status: VerificationSessionStatus;
  currentStep: VerificationStep;
  requiredDocumentTypes: string[];
  acceptedConsentAt?: string;
}

const sessionFixtures: Record<string, VerificationSession> = {
  "sess-12345": {
    sessionId: "sess-12345",
    organizationName: "Acme Corp",
    purpose: "Account opening and fraud-prevention checks for regulated onboarding.",
    status: "active",
    currentStep: "consent",
    requiredDocumentTypes: ["Passport", "National ID", "Driver's License"],
  },
  "sess-expired": {
    sessionId: "sess-expired",
    organizationName: "Acme Corp",
    purpose: "Identity re-verification for an expiring account review.",
    status: "expired",
    currentStep: "document",
    requiredDocumentTypes: ["Passport", "National ID"],
  },
  "sess-complete": {
    sessionId: "sess-complete",
    organizationName: "Acme Corp",
    purpose: "Repeat verification for high-value transaction approval.",
    status: "completed",
    currentStep: "complete",
    requiredDocumentTypes: ["Passport"],
    acceptedConsentAt: "2026-07-06T19:22:00Z",
  },
  "sess-error": {
    sessionId: "sess-error",
    organizationName: "Acme Corp",
    purpose: "Identity recovery after account security escalation.",
    status: "error",
    currentStep: "selfie",
    requiredDocumentTypes: ["National ID"],
  },
};

export async function fetchVerificationSession(sessionId: string): Promise<VerificationSession> {
  await delay(120);
  return (
    sessionFixtures[sessionId] ?? {
      ...sessionFixtures["sess-12345"],
      sessionId,
    }
  );
}

export async function submitVerificationStep(
  sessionId: string,
  nextStep: VerificationStep
): Promise<VerificationSession> {
  await delay(250);
  const session = await fetchVerificationSession(sessionId);

  return {
    ...session,
    currentStep: nextStep,
    status: nextStep === "complete" ? "completed" : "active",
    acceptedConsentAt: nextStep !== "consent" ? session.acceptedConsentAt ?? new Date().toISOString() : session.acceptedConsentAt,
  };
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
