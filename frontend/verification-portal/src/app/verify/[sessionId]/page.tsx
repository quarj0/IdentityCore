"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  Camera,
  CheckCircle2,
  Lock,
  ScanFace,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import {
  Badge,
  BrandMark,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Progress,
  cn,
} from "@identitycore/ui";

const STEPS = [
  { title: "Consent", description: "Review and accept processing terms" },
  { title: "Document", description: "Upload your identity document" },
  { title: "Selfie", description: "Capture a clear face image" },
  { title: "Liveness", description: "Confirm that you are present" },
  { title: "Complete", description: "Verification submitted" },
];

export default function VerificationSessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const resolvedParams = React.use(params);
  const [currentStep, setCurrentStep] = useState(0);
  const [documentType, setDocumentType] = useState("");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [selfieFile, setSelfieFile] = useState<File | null>(null);
  const [livenessPassed, setLivenessPassed] = useState(false);
  const [loading, setLoading] = useState(false);

  const progressPercentage = ((currentStep + 1) / STEPS.length) * 100;

  function nextStep() {
    setLoading(true);
    window.setTimeout(() => {
      setLoading(false);
      setCurrentStep((value) => Math.min(value + 1, STEPS.length - 1));
    }, 500);
  }

  function previousStep() {
    setCurrentStep((value) => Math.max(value - 1, 0));
  }

  return (
    <div className="min-h-screen bg-background px-4 py-6 md:px-6 md:py-8">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-6xl gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <section className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="space-y-8">
            <BrandMark subtitle="Secure verification session" size="lg" />

            <div className="space-y-4">
              <Badge variant="info" className="px-3 py-1">
                <ShieldCheck className="h-3.5 w-3.5" />
                Session {resolvedParams.sessionId}
              </Badge>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                Verify your identity for Acme Corp.
              </h1>
              <p className="text-sm leading-6 text-muted-foreground">
                This guided flow keeps the experience short while giving the reviewing team enough structured evidence to make a confident decision.
              </p>
            </div>

            <div className="space-y-2">
              {STEPS.map((step, index) => (
                <div
                  key={step.title}
                  className={cn(
                    "rounded-lg border p-4 transition-colors",
                    index === currentStep
                      ? "border-primary/40 bg-primary/5"
                      : index < currentStep
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-border bg-background"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                        index < currentStep
                          ? "bg-emerald-500 text-white"
                          : index === currentStep
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                      )}
                    >
                      {index < currentStep ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : (
                        index + 1
                      )}
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
              Your information is encrypted in transit and at rest. Only authorized reviewers at Acme Corp can access your submission.
            </div>
          </div>
        </section>

        <main className="flex items-stretch">
          <Card className="flex w-full flex-col overflow-hidden shadow-sm">
            <CardHeader className="space-y-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">{STEPS[currentStep].title}</CardTitle>
                  <CardDescription>{STEPS[currentStep].description}</CardDescription>
                </div>
                <Badge variant="outline">
                  Step {currentStep + 1} of {STEPS.length}
                </Badge>
              </div>
              <Progress value={progressPercentage} className="h-1.5" />
            </CardHeader>

            <CardContent className="flex-1 p-6">
              {currentStep === 0 ? (
                <div className="space-y-5">
                  <div className="rounded-lg border border-border bg-muted/40 p-5">
                    <div className="flex gap-3">
                      <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                      <div className="space-y-2">
                        <div className="font-semibold text-foreground">
                          Consent to identity processing
                        </div>
                        <p className="text-sm leading-6 text-muted-foreground">
                          Acme Corp uses IdentityCore to collect document and facial verification evidence. Continue only if you agree to the secure processing of this information for trust and compliance purposes.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-border p-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <Lock className="h-4 w-4 text-primary" />
                        Protected session
                      </div>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        All evidence remains encrypted during capture and review.
                      </p>
                    </div>
                    <div className="rounded-lg border border-border p-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <Sparkles className="h-4 w-4 text-primary" />
                        Guided flow
                      </div>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        The process adapts as you move forward so you only see what is needed.
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}

              {currentStep === 1 ? (
                <div className="space-y-6">
                  <div className="grid gap-3 sm:grid-cols-3">
                    {["Passport", "National ID", "Driver's License"].map((type) => (
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
                    <div className="mt-4 text-base font-semibold text-foreground">
                      Upload the front of your {documentType || "identity document"}
                    </div>
                    <div className="mt-2 text-sm text-muted-foreground">
                      PNG, JPG, or PDF up to 10MB
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      onChange={(event) => setDocumentFile(event.target.files?.[0] || null)}
                    />
                    {documentFile ? (
                      <div className="mt-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                        Selected: {documentFile.name}
                      </div>
                    ) : null}
                  </label>
                </div>
              ) : null}

              {currentStep === 2 ? (
                <div className="space-y-6 text-center">
                  <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full border-2 border-dashed border-primary/30 bg-primary/5">
                    <Camera className="h-8 w-8 text-primary" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-base font-semibold text-foreground">
                      Capture a clear selfie
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      Keep your face centered, avoid strong backlight, and remove anything that obscures the photo.
                    </p>
                  </div>
                  <label className="inline-flex cursor-pointer items-center gap-2">
                    <Button asChild>
                      <span>
                        <Camera className="h-4 w-4" />
                        Capture photo
                      </span>
                    </Button>
                    <input
                      type="file"
                      accept="image/*"
                      capture="user"
                      className="hidden"
                      onChange={(event) => setSelfieFile(event.target.files?.[0] || null)}
                    />
                  </label>
                  {selfieFile ? (
                    <div className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                      Selfie captured successfully
                    </div>
                  ) : null}
                </div>
              ) : null}

              {currentStep === 3 ? (
                <div className="space-y-6">
                  <div className="flex aspect-video items-center justify-center rounded-lg border border-border bg-sidebar text-center">
                    <div className="space-y-3 px-6">
                      <ScanFace className="mx-auto h-8 w-8 text-sidebar-primary" />
                      <div className="text-base font-semibold text-sidebar-foreground">
                        Liveness check
                      </div>
                      <p className="text-sm leading-6 text-sidebar-muted-foreground">
                        Position your face within the frame and follow the prompt to blink naturally.
                      </p>
                    </div>
                  </div>
                  {!livenessPassed ? (
                    <Button className="w-full" onClick={() => setLivenessPassed(true)}>
                      Start liveness check
                    </Button>
                  ) : (
                    <div className="flex items-center gap-3 rounded-lg bg-emerald-500/10 p-4 text-sm text-emerald-700 dark:text-emerald-300">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      Liveness check passed successfully
                    </div>
                  )}
                </div>
              ) : null}

              {currentStep === 4 ? (
                <div className="flex h-full flex-col items-center justify-center space-y-4 py-8 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-7 w-7" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xl font-semibold text-foreground">
                      Verification submitted
                    </div>
                    <p className="max-w-md text-sm leading-6 text-muted-foreground">
                      Acme Corp can now review your submission. You can safely close this tab.
                    </p>
                  </div>
                </div>
              ) : null}
            </CardContent>

            <CardFooter className="border-t border-border px-6 py-4">
              <div className="flex w-full items-center justify-between">
                {currentStep > 0 && currentStep < 4 ? (
                  <Button variant="outline" onClick={previousStep} disabled={loading}>
                    Back
                  </Button>
                ) : (
                  <div />
                )}

                {currentStep < 4 ? (
                  <Button
                    className="gap-2"
                    disabled={
                      loading ||
                      (currentStep === 1 && (!documentType || !documentFile)) ||
                      (currentStep === 2 && !selfieFile) ||
                      (currentStep === 3 && !livenessPassed)
                    }
                    onClick={nextStep}
                  >
                    {loading
                      ? "Processing..."
                      : currentStep === 0
                        ? "Accept and continue"
                        : "Continue"}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            </CardFooter>
          </Card>
        </main>
      </div>
    </div>
  );
}
