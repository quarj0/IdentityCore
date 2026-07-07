"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  Camera,
  Check,
  CheckCircle2,
  FileText,
  Loader2,
  ShieldCheck,
  Smile,
  Upload,
  Video,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Progress,
} from "@identitycore/ui";

const steps = [
  "Consent",
  "Document",
  "Selfie",
  "Liveness",
  "Processing",
  "Result",
];

const mockResult = {
  decision: "Approved",
  faceMatch: "98.7%",
  liveness: "Passed",
  ocrConfidence: "99.1%",
  documentAuthenticity: "Passed",
};

export function MockVerificationFlow() {
  const [step, setStep] = useState(0);

  const progress = useMemo(() => ((step + 1) / steps.length) * 100, [step]);

  const next = () =>
    setStep((current) => Math.min(current + 1, steps.length - 1));
  const back = () => setStep((current) => Math.max(current - 1, 0));

  return (
    <div className="grid gap-6 lg:grid-cols-[0.72fr_0.28fr]">
      <Card className="rounded-[2rem] border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>{steps[step]}</CardTitle>
              <CardDescription>Mock verification flow.</CardDescription>
            </div>

            <Badge variant="secondary" className="rounded-full">
              Step {step + 1} of {steps.length}
            </Badge>
          </div>

          <Progress value={progress} className="mt-5" />
        </CardHeader>

        <CardContent>{renderStep(step, next, back)}</CardContent>
      </Card>

      <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <CardTitle>Verification progress</CardTitle>
          <CardDescription>
            This preview simulates the verification experience and shows how
            IdentityCore presents each step.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3">
          {steps.map((item, index) => (
            <div
              key={item}
              className={
                index === step
                  ? "flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-3"
                  : index < step
                    ? "flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3"
                    : "flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3"
              }
            >
              <div
                className={
                  index < step
                    ? "flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white"
                    : "flex h-8 w-8 items-center justify-center rounded-xl bg-white text-slate-600 ring-1 ring-slate-200"
                }
              >
                {index < step ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <span className="text-xs font-semibold">{index + 1}</span>
                )}
              </div>
              <p className="text-sm font-medium">{item}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function renderStep(step: number, next: () => void, back: () => void) {
  if (step === 0) {
    return (
      <StepShell
        icon={<ShieldCheck className="h-6 w-6" />}
        title="Consent to administrator verification"
        description="Confirm that IdentityCore may process your identity evidence for workspace onboarding."
      >
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="space-y-3">
            {[
              "You are the person creating this workspace.",
              "You are submitting your own identity document.",
              "IdentityCore may process this evidence for onboarding review.",
              "This is currently a mock verification flow.",
            ].map((item) => (
              <div
                key={item}
                className="flex gap-3 text-sm text-muted-foreground"
              >
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <Button onClick={next} size="lg" className="rounded-xl">
          Accept and continue
          <ArrowRight className="h-4 w-4" />
        </Button>
      </StepShell>
    );
  }

  if (step === 1) {
    return (
      <StepShell
        icon={<FileText className="h-6 w-6" />}
        title="Capture your identity document"
        description="Upload or capture a supported identity document. This UI currently simulates capture."
      >
        <MockCaptureArea label="Document camera preview" icon={<Upload />} />

        <StepActions
          onBack={back}
          onNext={next}
          nextLabel="Use mock document"
        />
      </StepShell>
    );
  }

  if (step === 2) {
    return (
      <StepShell
        icon={<Camera className="h-6 w-6" />}
        title="Capture your selfie"
        description="Take a clear selfie so IdentityCore can compare your face with the document portrait."
      >
        <MockCaptureArea label="Selfie camera preview" icon={<Smile />} />

        <StepActions onBack={back} onNext={next} nextLabel="Use mock selfie" />
      </StepShell>
    );
  }

  if (step === 3) {
    return (
      <StepShell
        icon={<Video className="h-6 w-6" />}
        title="Complete liveness check"
        description="Complete a short liveness challenge. This preview simulates the result."
      >
        <div className="rounded-[2rem] border border-slate-200 bg-slate-950 p-8 text-center text-white">
          <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-full bg-white/10 ring-1 ring-white/10">
            <Smile className="h-12 w-12 text-blue-300" />
          </div>
          <p className="mt-6 text-sm font-medium">Challenge: Blink twice</p>
          <p className="mt-2 text-sm text-slate-400">
            Mock liveness challenge ready.
          </p>
        </div>

        <StepActions
          onBack={back}
          onNext={next}
          nextLabel="Pass mock liveness"
        />
      </StepShell>
    );
  }

  if (step === 4) {
    return (
      <StepShell
        icon={<Loader2 className="h-6 w-6 animate-spin" />}
        title="Processing verification evidence"
        description="IdentityCore is simulating OCR, face matching, liveness, policy evaluation, and decisioning."
      >
        <div className="space-y-3">
          {[
            "Reading document data",
            "Checking document quality",
            "Comparing document face with selfie",
            "Evaluating liveness evidence",
            "Applying administrator verification policy",
          ].map((item) => (
            <div
              key={item}
              className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <CheckCircle2 className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium">{item}</span>
            </div>
          ))}
        </div>

        <StepActions onBack={back} onNext={next} nextLabel="View mock result" />
      </StepShell>
    );
  }

  return (
    <StepShell
      icon={<CheckCircle2 className="h-6 w-6" />}
      title="Administrator verified"
      description="This mock result shows how IdentityCore will present verification evidence and decision outcomes."
    >
      <div className="rounded-[2rem] border border-blue-100 bg-blue-50 p-6">
        <p className="text-sm font-medium text-blue-700">Decision</p>
        <p className="mt-2 text-4xl font-semibold tracking-tight text-blue-950">
          {mockResult.decision}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {[
          ["Face match", mockResult.faceMatch],
          ["Liveness", mockResult.liveness],
          ["OCR confidence", mockResult.ocrConfidence],
          ["Document authenticity", mockResult.documentAuthenticity],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-2xl border border-slate-200 bg-white p-4"
          >
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-1 font-semibold">{value}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button size="lg" className="rounded-xl">
          Continue onboarding
          <ArrowRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="rounded-xl"
          onClick={back}
        >
          Back
        </Button>
      </div>
    </StepShell>
  );
}

function StepShell({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
        {icon}
      </div>

      <div>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        <p className="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground">
          {description}
        </p>
      </div>

      {children}
    </div>
  );
}

function MockCaptureArea({
  label,
  icon,
}: {
  label: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-slate-950 p-8 text-center text-white">
      <div className="mx-auto flex h-40 max-w-sm items-center justify-center rounded-3xl border border-white/10 bg-white/[0.04]">
        <div>
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-blue-300">
            {icon}
          </div>
          <p className="text-sm font-medium">{label}</p>
          <p className="mt-1 text-xs text-slate-400">
            Camera simulation for preview
          </p>
        </div>
      </div>
    </div>
  );
}

function StepActions({
  onBack,
  onNext,
  nextLabel,
}: {
  onBack: () => void;
  onNext: () => void;
  nextLabel: string;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <Button onClick={onNext} size="lg" className="rounded-xl">
        {nextLabel}
        <ArrowRight className="h-4 w-4" />
      </Button>
      <Button
        onClick={onBack}
        variant="outline"
        size="lg"
        className="rounded-xl"
      >
        Back
      </Button>
    </div>
  );
}
