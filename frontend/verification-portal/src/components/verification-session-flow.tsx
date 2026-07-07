"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Badge, BrandMark, Card, CardContent, CardDescription, CardHeader, CardTitle, Progress } from "@identitycore/ui";
import {
  CompleteInlineStep,
  ConsentStep,
  DocumentStep,
  LivenessStep,
  SelfieStep,
  SessionSidebar,
  SubmittingStep,
} from "@/components/session-steps";
import { submitVerificationStep, type VerificationSession, type VerificationStep } from "@/lib/session-api";

const STEPS = [
  { key: "consent", title: "Consent", description: "Review and accept processing terms" },
  { key: "document", title: "Document", description: "Upload your identity document" },
  { key: "selfie", title: "Selfie", description: "Capture a clear face image" },
  { key: "liveness", title: "Liveness", description: "Confirm that you are present" },
  { key: "submitting", title: "Submitting", description: "Securely sending your verification" },
  { key: "complete", title: "Complete", description: "Verification submitted" },
] as const;

const stepIndexMap: Record<VerificationStep, number> = {
  consent: 0,
  document: 1,
  selfie: 2,
  liveness: 3,
  submitting: 4,
  complete: 5,
};

export function VerificationSessionFlow({ initialSession }: { initialSession: VerificationSession }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [session, setSession] = useState(initialSession);
  const [documentType, setDocumentType] = useState("");
  const [documentFileName, setDocumentFileName] = useState<string | null>(null);
  const [selfieReady, setSelfieReady] = useState(false);
  const [livenessPassed, setLivenessPassed] = useState(false);

  const currentStepIndex = stepIndexMap[session.currentStep];
  const progressPercentage = ((currentStepIndex + 1) / STEPS.length) * 100;

  useEffect(() => {
    if (session.status === "completed") {
      router.replace(`/verify/${session.sessionId}/complete`);
    }
    if (session.status === "error") {
      router.replace(`/verify/${session.sessionId}/error`);
    }
  }, [router, session.sessionId, session.status]);

  const currentStep = useMemo(() => STEPS[currentStepIndex], [currentStepIndex]);

  function goNext(nextStep: VerificationStep) {
    startTransition(async () => {
      const nextSession = await submitVerificationStep(session.sessionId, nextStep);
      setSession(nextSession);

      if (nextStep === "submitting") {
        const completedSession = await submitVerificationStep(session.sessionId, "complete");
        setSession(completedSession);
      }
    });
  }

  function goBack() {
    const previousStepIndex = Math.max(currentStepIndex - 1, 0);
    setSession((prev) => ({ ...prev, currentStep: STEPS[previousStepIndex].key }));
  }

  return (
    <div className="min-h-screen bg-background px-4 py-6 md:px-6 md:py-8">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-6xl gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <SessionSidebar session={session} currentStepIndex={currentStepIndex} steps={STEPS} />

        <main id="main-content" className="flex items-stretch">
          <Card className="flex w-full flex-col overflow-hidden shadow-sm">
            <CardHeader className="space-y-4 border-b border-border">
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <BrandMark subtitle="Secure verification session" size="sm" />
                  </div>
                  <CardTitle className="text-xl">{currentStep.title}</CardTitle>
                  <CardDescription>{currentStep.description}</CardDescription>
                </div>
                <Badge variant="outline">Step {currentStepIndex + 1} of {STEPS.length}</Badge>
              </div>
              <Progress value={progressPercentage} className="h-1.5" />
            </CardHeader>

            <CardContent className="flex-1 p-6">
              {session.currentStep === "consent" ? <ConsentStep session={session} onContinue={() => goNext("document")} disabled={isPending} /> : null}
              {session.currentStep === "document" ? (
                <DocumentStep
                  session={session}
                  onBack={goBack}
                  onContinue={() => goNext("selfie")}
                  disabled={isPending}
                  documentType={documentType}
                  setDocumentType={setDocumentType}
                  documentFileName={documentFileName}
                  setDocumentFileName={setDocumentFileName}
                />
              ) : null}
              {session.currentStep === "selfie" ? (
                <SelfieStep
                  session={session}
                  onBack={goBack}
                  onContinue={() => goNext("liveness")}
                  disabled={isPending}
                  selfieReady={selfieReady}
                  setSelfieReady={setSelfieReady}
                />
              ) : null}
              {session.currentStep === "liveness" ? (
                <LivenessStep
                  session={session}
                  onBack={goBack}
                  onContinue={() => goNext("submitting")}
                  disabled={isPending}
                  livenessPassed={livenessPassed}
                  setLivenessPassed={setLivenessPassed}
                />
              ) : null}
              {session.currentStep === "submitting" ? <SubmittingStep /> : null}
              {session.currentStep === "complete" ? <CompleteInlineStep session={session} /> : null}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
