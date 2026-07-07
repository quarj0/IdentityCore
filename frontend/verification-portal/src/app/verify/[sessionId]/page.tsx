"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Camera,
  Upload,
  CheckCircle2,
  Lock,
  ArrowRight,
  Fingerprint,
  FileText,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Progress,
  Badge,
} from "@identitycore/ui";

const STEPS = [
  { title: "Consent", description: "Review and accept terms" },
  { title: "Document", description: "Upload identity document" },
  { title: "Selfie", description: "Capture a clear portrait" },
  { title: "Liveness", description: "Verify you are present" },
  { title: "Complete", description: "Verification submitted" },
];

export default function VerificationSessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const resolvedParams = React.use(params);
  const [currentStep, setCurrentStep] = useState(0);
  const [documentType, setDocumentType] = useState<string>("");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [selfieFile, setSelfieFile] = useState<File | null>(null);
  const [livenessSuccess, setLivenessSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const progressPercentage = ((currentStep + 1) / STEPS.length) * 100;

  const nextStep = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }, 800);
  };

  const prevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50 dark:bg-slate-900 px-4 py-8">
      {/* Top logo/branding */}
      <header className="flex flex-col items-center justify-center max-w-md mx-auto w-full mb-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white dark:bg-white dark:text-slate-900">
            <Fingerprint className="h-5 w-5" />
          </div>
          <span className="font-semibold text-lg tracking-tight text-slate-900 dark:text-white">
            IdentityCore
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Secure verification session for <span className="font-medium text-foreground">Acme Corp</span>
        </p>
      </header>

      {/* Main card */}
      <main className="flex-1 flex items-center justify-center w-full max-w-md mx-auto">
        <Card className="w-full border-slate-200/60 dark:border-slate-800/80 shadow-md bg-white dark:bg-slate-950">
          <CardHeader className="pb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Step {currentStep + 1} of {STEPS.length}
              </span>
              <Badge variant="outline" className="text-xs">
                {STEPS[currentStep].title}
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold">{STEPS[currentStep].title}</CardTitle>
            <CardDescription className="text-sm">
              {STEPS[currentStep].description}
            </CardDescription>
            <Progress value={progressPercentage} className="h-1.5 mt-3" />
          </CardHeader>

          <CardContent className="space-y-4 min-h-[220px] flex flex-col justify-center">
            {/* Step 1: Consent */}
            {currentStep === 0 && (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Acme Corp uses IdentityCore to securely verify your identity. By clicking "Accept and Continue", you consent to the processing of your biometric and document data in accordance with our Privacy Policy.
                </p>
                <div className="rounded-lg bg-slate-50 dark:bg-slate-900 p-3 space-y-2 border border-slate-100 dark:border-slate-800">
                  <div className="flex gap-2 items-start text-xs">
                    <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                    <span>Your data is encrypted end-to-end and stored securely.</span>
                  </div>
                  <div className="flex gap-2 items-start text-xs">
                    <Lock className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                    <span>Only authorized officers at Acme Corp can review your submission.</span>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Document */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  {["Passport", "National ID", "Driver's License"].map((type) => (
                    <button
                      key={type}
                      onClick={() => setDocumentType(type)}
                      className={`p-3 rounded-lg border text-xs font-medium transition-all ${
                        documentType === type
                          ? "border-primary bg-primary/5 text-primary"
                          : "border-border bg-transparent hover:bg-muted/50 text-muted-foreground"
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>

                {documentType && (
                  <div className="border border-dashed border-slate-300 dark:border-slate-800 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                    <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                    <span className="text-xs font-medium text-foreground">Upload the front of your {documentType}</span>
                    <span className="text-[10px] text-muted-foreground mt-1">PNG, JPG or PDF up to 10MB</span>
                    <input
                      type="file"
                      className="hidden"
                      id="doc-upload"
                      onChange={(e) => setDocumentFile(e.target.files?.[0] || null)}
                    />
                    <label htmlFor="doc-upload" className="mt-3 text-xs bg-secondary text-secondary-foreground px-3 py-1.5 rounded-md cursor-pointer hover:bg-secondary/80">
                      Select File
                    </label>
                    {documentFile && (
                      <span className="text-xs text-emerald-600 dark:text-emerald-400 mt-2 font-medium">
                        ✓ {documentFile.name}
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Selfie */}
            {currentStep === 2 && (
              <div className="space-y-4 flex flex-col items-center">
                <div className="h-32 w-32 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center relative overflow-hidden">
                  <Camera className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="text-center space-y-1">
                  <p className="text-xs font-medium">Take a photo of yourself</p>
                  <p className="text-[11px] text-muted-foreground">Make sure your face is well-lit, not blurry, and fully visible.</p>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  capture="user"
                  className="hidden"
                  id="selfie-capture"
                  onChange={(e) => setSelfieFile(e.target.files?.[0] || null)}
                />
                <label htmlFor="selfie-capture" className="text-xs bg-primary text-primary-foreground px-4 py-2 rounded-md cursor-pointer hover:bg-primary/90 flex items-center gap-1.5">
                  <Camera className="h-4 w-4" />
                  Capture Photo
                </label>
                {selfieFile && (
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    ✓ Photo captured successfully
                  </span>
                )}
              </div>
            )}

            {/* Step 4: Liveness */}
            {currentStep === 3 && (
              <div className="space-y-4 flex flex-col items-center">
                <div className="w-full aspect-video rounded-lg bg-slate-950 flex items-center justify-center relative overflow-hidden border border-slate-800">
                  <div className="absolute inset-0 border-2 border-primary/40 rounded-lg animate-pulse" />
                  <div className="text-center z-10 px-4 space-y-2">
                    <Sparkles className="h-6 w-6 text-primary mx-auto animate-bounce" />
                    <p className="text-xs text-slate-300">Position your face within the frame and blink when prompted.</p>
                  </div>
                </div>

                {!livenessSuccess ? (
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => setLivenessSuccess(true)}
                  >
                    Start Liveness Check
                  </Button>
                ) : (
                  <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    Liveness check passed successfully
                  </div>
                )}
              </div>
            )}

            {/* Step 5: Complete */}
            {currentStep === 4 && (
              <div className="text-center space-y-3 py-4">
                <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-base">All Steps Completed</h3>
                  <p className="text-xs text-muted-foreground">Your identity verification has been securely submitted to Acme Corp for review. You may close this tab now.</p>
                </div>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex justify-between border-t border-border pt-4">
            {currentStep > 0 && currentStep < 4 ? (
              <Button variant="outline" size="sm" onClick={prevStep} disabled={loading}>
                Back
              </Button>
            ) : (
              <div />
            )}

            {currentStep < 4 && (
              <Button
                size="sm"
                className="gap-1.5"
                disabled={
                  loading ||
                  (currentStep === 1 && (!documentType || !documentFile)) ||
                  (currentStep === 2 && !selfieFile) ||
                  (currentStep === 3 && !livenessSuccess)
                }
                onClick={nextStep}
              >
                {loading ? "Processing..." : currentStep === 0 ? "Accept and Continue" : "Continue"}
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            )}
          </CardFooter>
        </Card>
      </main>

      {/* Footer secure label */}
      <footer className="text-center mt-6 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
        <Lock className="h-3 w-3" />
        <span>Secured by IdentityCore end-to-end encryption.</span>
      </footer>
    </div>
  );
}
