"use client";

import { useState } from "react";
import type { VerificationStep } from "@/data/verification";
import { CaptureReviewStep } from "./capture-review-step";
import { ConsentStep } from "./consent-step";
import { DocumentCaptureStep } from "./document-capture-step";
import { DocumentTypeStep } from "./document-type-step";
import { LivenessStep } from "./liveness-step";
import { ProcessingStep } from "./processing-step";
import { SelfieCaptureStep } from "./selfie-capture-step";
import { SessionExpiredInline } from "./session-expired-inline";
import { SubmittedStep } from "./submitted-step";
import { UploadFallback } from "./upload-fallback";
import { VerificationProgress } from "./verification-progress";
import { ResultStep } from "./result-step";

export function VerificationFlow() {
  const [step, setStep] = useState<VerificationStep>("consent");
  const [expired, setExpired] = useState(false);
  const [documentType, setDocumentType] = useState("National ID");
  const [uploadMode, setUploadMode] = useState<null | VerificationStep>(null);
  const [resultState, setResultState] = useState<
    "approved" | "review" | "rejected"
  >("approved");

  if (expired) {
    return <SessionExpiredInline />;
  }

  if (uploadMode) {
    return (
      <UploadFallback
        title="Upload evidence"
        description="Upload fallback for this capture step."
        onBackToCamera={() => setUploadMode(null)}
        onUploaded={() => {
          const current = uploadMode;
          setUploadMode(null);

          if (current === "document_front") setStep("document_back");
          if (current === "document_back") setStep("document_review");
          if (current === "selfie") setStep("selfie_review");
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <VerificationProgress currentStep={step} />

      {step === "consent" ? (
        <ConsentStep
          onNext={() => setStep("document_type")}
          onExpire={() => setExpired(true)}
        />
      ) : null}

      {step === "document_type" ? (
        <DocumentTypeStep
          onBack={() => setStep("consent")}
          onNext={(type) => {
            setDocumentType(type);
            setStep("document_front");
          }}
        />
      ) : null}

      {step === "document_front" ? (
        <DocumentCaptureStep
          side="front"
          documentType={documentType}
          onBack={() => setStep("document_type")}
          onUpload={() => setUploadMode("document_front")}
          onCapture={() => setStep("document_back")}
        />
      ) : null}

      {step === "document_back" ? (
        <DocumentCaptureStep
          side="back"
          documentType={documentType}
          onBack={() => setStep("document_front")}
          onUpload={() => setUploadMode("document_back")}
          onCapture={() => setStep("document_review")}
        />
      ) : null}

      {step === "document_review" ? (
        <CaptureReviewStep
          title="Review document captures"
          description="Confirm the captured document images are readable before continuing."
          items={[
            `${documentType} front captured`,
            `${documentType} back captured`,
            "Document is readable",
            "All corners are visible",
          ]}
          onBack={() => setStep("document_back")}
          onRetry={() => setStep("document_front")}
          onNext={() => setStep("selfie")}
        />
      ) : null}

      {step === "selfie" ? (
        <SelfieCaptureStep
          onBack={() => setStep("document_review")}
          onUpload={() => setUploadMode("selfie")}
          onCapture={() => setStep("selfie_review")}
        />
      ) : null}

      {step === "selfie_review" ? (
        <CaptureReviewStep
          title="Review selfie"
          description="Confirm your selfie is clear before continuing."
          items={[
            "Face is visible",
            "Lighting looks clear",
            "No major obstruction detected",
          ]}
          onBack={() => setStep("selfie")}
          onRetry={() => setStep("selfie")}
          onNext={() => setStep("liveness")}
        />
      ) : null}

      {step === "liveness" ? (
        <LivenessStep
          onBack={() => setStep("selfie_review")}
          onNext={() => setStep("processing")}
        />
      ) : null}

      {step === "processing" ? (
        <ProcessingStep
          onResult={(state) => {
            setResultState(state);
            setStep("result");
          }}
        />
      ) : null}

      {step === "result" ? (
        <ResultStep state={resultState} onSubmit={() => setStep("submitted")} />
      ) : null}

      {step === "submitted" ? <SubmittedStep /> : null}
    </div>
  );
}
