"use client";

import { useState } from "react";
import {
  ArrowRight,
  Check,
  Loader2,
  ShieldCheck,
  Smile,
  Video,
} from "lucide-react";
import { Button, Checkbox, Label } from "@identitycore/ui";
import { CameraPermission } from "./camera-permission";
import { CameraUnavailable } from "./camera-unavailable";
import { CapturePanel } from "./capture-panel";
import { MockCamera } from "./mock-camera";
import { ResultSummary } from "./result-summary";
import { RetryPanel } from "./retry-panel";
import { SessionExpiredInline } from "./session-expired-inline";
import { UploadFallback } from "./upload-fallback";
import { VerificationProgress } from "./verification-progress";

type CaptureMode = "permission" | "camera" | "denied" | "upload" | "retry";

export function VerificationFlow() {
  const [step, setStep] = useState(0);
  const [documentMode, setDocumentMode] = useState<CaptureMode>("permission");
  const [selfieMode, setSelfieMode] = useState<CaptureMode>("permission");
  const [livenessRetry, setLivenessRetry] = useState(false);
  const [expired, setExpired] = useState(false);
  const [resultState, setResultState] = useState<
    "approved" | "review" | "rejected"
  >("approved");

  const next = () => setStep((value) => Math.min(value + 1, 5));
  const back = () => setStep((value) => Math.max(value - 1, 0));

  if (expired) {
    return <SessionExpiredInline />;
  }

  return (
    <div className="space-y-6">
      <VerificationProgress currentStep={step} />

      {step === 0 ? (
        <CapturePanel
          title="Consent to identity verification"
          description="Review why your identity is being verified before continuing."
        >
          <div className="space-y-5">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex gap-3">
                <ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-blue-600" />
                <div>
                  <p className="text-sm font-medium">What will be processed</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                    <li>Identity document image</li>
                    <li>Selfie image</li>
                    <li>Liveness evidence</li>
                    <li>Verification metadata and audit events</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4">
              <Checkbox id="consent" className="mt-1" />
              <Label
                htmlFor="consent"
                className="text-sm leading-6 text-slate-600"
              >
                I consent to this organization using IdentityCore to process my
                identity evidence for this verification workflow.
              </Label>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={next} size="lg" className="rounded-xl">
                Continue
                <ArrowRight className="h-4 w-4" />
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() => setExpired(true)}
                size="lg"
                className="rounded-xl"
              >
                Simulate expired session
              </Button>
            </div>
          </div>
        </CapturePanel>
      ) : null}

      {step === 1 ? (
        <CapturePanel
          title="Capture your identity document"
          description="Use a clear, readable government-issued identity document."
        >
          <CaptureState
            mode={documentMode}
            setMode={setDocumentMode}
            cameraLabel="Document capture"
            uploadTitle="Upload identity document"
            uploadDescription="Upload a clear image of your supported identity document."
            onComplete={() => setDocumentMode("retry")}
            onContinue={next}
          />

          <StepBack onBack={back} />
        </CapturePanel>
      ) : null}

      {step === 2 ? (
        <CapturePanel
          title="Capture your selfie"
          description="Take a clear selfie so your face can be compared with the identity document."
        >
          <CaptureState
            mode={selfieMode}
            setMode={setSelfieMode}
            cameraLabel="Selfie capture"
            uploadTitle="Upload selfie"
            uploadDescription="Upload a clear selfie image for mock face matching."
            onComplete={() => setSelfieMode("retry")}
            onContinue={next}
          />

          <StepBack onBack={back} />
        </CapturePanel>
      ) : null}

      {step === 3 ? (
        <CapturePanel
          title="Complete liveness check"
          description="Complete a short liveness challenge to confirm a real person is present."
        >
          {livenessRetry ? (
            <RetryPanel
              title="Liveness quality warning"
              description="The mock liveness evidence was not clear enough. You can retry or continue with mock evidence."
              onRetry={() => setLivenessRetry(false)}
              onContinue={next}
            />
          ) : (
            <div className="rounded-[2rem] bg-slate-950 p-8 text-center text-white">
              <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-white/10">
                <Smile className="h-14 w-14 text-blue-300" />
              </div>
              <p className="mt-6 text-sm font-medium">Challenge: Blink twice</p>
              <p className="mt-2 text-sm text-slate-400">
                Mock liveness challenge
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <Button onClick={next} className="rounded-xl">
                  <Video className="h-4 w-4" />
                  Pass mock liveness
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setLivenessRetry(true)}
                  className="rounded-xl border-white/10 bg-white/5 text-white hover:bg-white/10"
                >
                  Simulate retry
                </Button>
              </div>
            </div>
          )}

          <StepBack onBack={back} />
        </CapturePanel>
      ) : null}

      {step === 4 ? (
        <CapturePanel
          title="Processing your verification"
          description="IdentityCore is simulating document analysis, face match, liveness, and policy decisioning."
        >
          <div className="space-y-3">
            {[
              "Reading document fields",
              "Checking document authenticity",
              "Comparing document face with selfie",
              "Evaluating liveness evidence",
              "Applying workflow policy",
            ].map((item) => (
              <div
                key={item}
                className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <Check className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium">{item}</span>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Button
              onClick={() => {
                setResultState("approved");
                next();
              }}
              className="rounded-xl"
            >
              <Loader2 className="h-4 w-4 animate-spin" />
              Approved
            </Button>

            <Button
              variant="outline"
              onClick={() => {
                setResultState("review");
                next();
              }}
              className="rounded-xl"
            >
              Needs review
            </Button>

            <Button
              variant="outline"
              onClick={() => {
                setResultState("rejected");
                next();
              }}
              className="rounded-xl"
            >
              Rejected
            </Button>
          </div>
        </CapturePanel>
      ) : null}

      {step === 5 ? (
        <CapturePanel
          title="Verification complete"
          description="This mock result shows the decision and evidence summary returned by the workflow."
        >
          <ResultSummary state={resultState} />
        </CapturePanel>
      ) : null}
    </div>
  );
}

function CaptureState({
  mode,
  setMode,
  cameraLabel,
  uploadTitle,
  uploadDescription,
  onComplete,
  onContinue,
}: {
  mode: CaptureMode;
  setMode: (mode: CaptureMode) => void;
  cameraLabel: string;
  uploadTitle: string;
  uploadDescription: string;
  onComplete: () => void;
  onContinue: () => void;
}) {
  if (mode === "permission") {
    return (
      <CameraPermission
        onAllow={() => setMode("camera")}
        onDenied={() => setMode("denied")}
      />
    );
  }

  if (mode === "denied") {
    return (
      <CameraUnavailable
        onRetry={() => setMode("permission")}
        onUpload={() => setMode("upload")}
      />
    );
  }

  if (mode === "upload") {
    return (
      <UploadFallback
        title={uploadTitle}
        description={uploadDescription}
        onBackToCamera={() => setMode("permission")}
        onUploaded={onComplete}
      />
    );
  }

  if (mode === "retry") {
    return (
      <RetryPanel
        title="Image quality warning"
        description="The mock capture was flagged as low quality. You can retry or continue with the captured evidence."
        onRetry={() => setMode("camera")}
        onContinue={onContinue}
      />
    );
  }

  return (
    <MockCamera
      label={cameraLabel}
      onUpload={() => setMode("upload")}
      onCapture={onComplete}
    />
  );
}

function StepBack({ onBack }: { onBack: () => void }) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onBack}
      className="mt-4 rounded-xl"
    >
      Back
    </Button>
  );
}
