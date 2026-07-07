"use client";

import { Camera, CheckCircle2, Lock, ScanFace, ShieldCheck, Sparkles, Upload } from "lucide-react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, cn } from "@identitycore/ui";
import type { VerificationSession } from "@/lib/session-api";

interface BaseStepProps {
  session: VerificationSession;
  onContinue: () => void;
  onBack?: () => void;
  disabled?: boolean;
}

export function ConsentStep({ session, onContinue, disabled }: BaseStepProps) {
  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-border bg-muted/40 p-5">
        <div className="flex gap-3">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
          <div className="space-y-2">
            <div className="font-semibold text-foreground">Consent to identity processing</div>
            <p className="text-sm leading-6 text-muted-foreground">
              {session.organizationName} uses IdentityCore to collect identity evidence for {session.purpose.toLowerCase()}
            </p>
          </div>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <InfoCard title="Protected session" description="All evidence remains encrypted during capture and review." icon={<Lock className="h-4 w-4 text-primary" />} />
        <InfoCard title="Guided flow" description="You only see the steps that are required for this verification." icon={<Sparkles className="h-4 w-4 text-primary" />} />
      </div>
      <div className="flex justify-end">
        <Button onClick={onContinue} disabled={disabled}>Accept and continue</Button>
      </div>
    </div>
  );
}

export function DocumentStep({
  session,
  onContinue,
  onBack,
  disabled,
  documentType,
  setDocumentType,
  documentFileName,
  setDocumentFileName,
}: BaseStepProps & {
  documentType: string;
  setDocumentType: (value: string) => void;
  documentFileName: string | null;
  setDocumentFileName: (value: string | null) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-3">
        {session.requiredDocumentTypes.map((type) => (
          <button
            key={type}
            onClick={() => setDocumentType(type)}
            className={cn(
              "rounded-lg border p-4 text-sm font-medium transition-colors",
              documentType === type
                ? "border-primary bg-primary/5 text-primary"
                : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {type}
          </button>
        ))}
      </div>

      <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center transition-colors hover:bg-muted/50">
        <Upload className="h-8 w-8 text-primary" />
        <div className="mt-4 text-base font-semibold text-foreground">Upload the front of your {documentType || "identity document"}</div>
        <div className="mt-2 text-sm text-muted-foreground">PNG, JPG, or PDF up to 10MB</div>
        <input
          type="file"
          className="hidden"
          onChange={(event) => setDocumentFileName(event.target.files?.[0]?.name ?? null)}
        />
        {documentFileName ? (
          <div className="mt-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">Selected: {documentFileName}</div>
        ) : null}
      </label>

      <StepActions onBack={onBack} onContinue={onContinue} disabled={disabled || !documentType || !documentFileName} />
    </div>
  );
}

export function SelfieStep({
  onContinue,
  onBack,
  disabled,
  selfieReady,
  setSelfieReady,
}: BaseStepProps & {
  selfieReady: boolean;
  setSelfieReady: (value: boolean) => void;
}) {
  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full border-2 border-dashed border-primary/30 bg-primary/5">
        <Camera className="h-8 w-8 text-primary" />
      </div>
      <div className="space-y-2">
        <div className="text-base font-semibold text-foreground">Capture a clear selfie</div>
        <p className="text-sm leading-6 text-muted-foreground">
          Keep your face centered, avoid strong backlight, and remove anything that obscures the photo.
        </p>
      </div>
      <Button variant={selfieReady ? "outline" : "default"} onClick={() => setSelfieReady(true)}>
        {selfieReady ? "Selfie captured" : "Simulate selfie capture"}
      </Button>
      <StepActions onBack={onBack} onContinue={onContinue} disabled={disabled || !selfieReady} />
    </div>
  );
}

export function LivenessStep({
  onContinue,
  onBack,
  disabled,
  livenessPassed,
  setLivenessPassed,
}: BaseStepProps & {
  livenessPassed: boolean;
  setLivenessPassed: (value: boolean) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-muted/40 p-6">
        <div className="flex items-start gap-3">
          <ScanFace className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
          <div>
            <div className="font-semibold text-foreground">Complete a short liveness check</div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              We use this step to make sure a real person is present during the session.
            </p>
          </div>
        </div>
      </div>
      <Button onClick={() => setLivenessPassed(true)}>{livenessPassed ? "Liveness passed" : "Simulate liveness pass"}</Button>
      <StepActions onBack={onBack} onContinue={onContinue} disabled={disabled || !livenessPassed} />
    </div>
  );
}

export function SubmittingStep() {
  return (
    <div className="space-y-4 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
        <ShieldCheck className="h-8 w-8" />
      </div>
      <div>
        <div className="text-lg font-semibold text-foreground">Submitting your verification</div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          We are packaging your evidence securely and sending it for review.
        </p>
      </div>
    </div>
  );
}

export function CompleteInlineStep({ session }: { session: VerificationSession }) {
  return (
    <div className="space-y-4 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600">
        <CheckCircle2 className="h-8 w-8" />
      </div>
      <div>
        <div className="text-lg font-semibold text-foreground">Verification submitted</div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {session.organizationName} can now review your submission and follow up if any extra information is needed.
        </p>
      </div>
    </div>
  );
}

function StepActions({
  onBack,
  onContinue,
  disabled,
}: {
  onBack?: () => void;
  onContinue: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <Button variant="outline" onClick={onBack} disabled={!onBack}>Back</Button>
      <Button onClick={onContinue} disabled={disabled}>Continue</Button>
    </div>
  );
}

function InfoCard({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="space-y-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          {icon}
          {title}
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  );
}

export function SessionSidebar({
  session,
  currentStepIndex,
  steps,
}: {
  session: VerificationSession;
  currentStepIndex: number;
  steps: readonly { title: string; description: string }[];
}) {
  return (
    <section className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="space-y-8">
        <div className="space-y-4">
          <Badge variant="info" className="px-3 py-1">
            <ShieldCheck className="h-3.5 w-3.5" />
            Session {session.sessionId}
          </Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Verify your identity for {session.organizationName}
          </h1>
          <p className="text-sm leading-6 text-muted-foreground">
            This guided flow keeps the experience short while giving the reviewing team enough structured evidence to make a confident decision.
          </p>
        </div>

        <div className="space-y-2">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className={cn(
                "rounded-lg border p-4 transition-colors",
                index === currentStepIndex
                  ? "border-primary/40 bg-primary/5"
                  : index < currentStepIndex
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-border bg-background"
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                    index < currentStepIndex
                      ? "bg-emerald-500 text-white"
                      : index === currentStepIndex
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                  )}
                >
                  {index < currentStepIndex ? <CheckCircle2 className="h-3.5 w-3.5" /> : index + 1}
                </div>
                <div>
                  <div className="font-medium text-foreground">{step.title}</div>
                  <div className="text-sm text-muted-foreground">{step.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-lg bg-muted/60 p-4 text-sm leading-6 text-muted-foreground">
          Your information is encrypted in transit and at rest. Only authorized reviewers at {session.organizationName} can access your submission.
        </div>
      </div>
    </section>
  );
}
