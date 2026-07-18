"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Check,
  Copy,
  FileText,
  Loader2,
  LockKeyhole,
  Monitor,
  ScanFace,
  ShieldCheck,
  Smartphone,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

import { Button, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

import {
  acceptConsent,
  clearSessionCredentials,
  consumeSessionCredentials,
  createMobileHandoff,
  createUpload,
  fetchVerificationSession,
  fetchVerificationStatus,
  redeemMobileHandoff,
  submitDocument,
  submitLiveness,
  submitSelfie,
  type SessionCredentials,
  type VerificationSession,
  type VerificationStatus,
} from "@/lib/session-api";

import { CameraCapture } from "./camera-capture";
import {
  EvidenceReview,
  ProcessingPanel,
  StepCard,
  TerminalPanel,
} from "./verification-panels";
import { VerificationFrame } from "./verification-frame";

const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const PROCESSING_STEPS = new Set(["document_processing", "processing"]);

export function LiveVerificationFlow({
  sessionId,
  handoff,
}: {
  sessionId: string;
  handoff?: string;
}) {
  const [credentials, setCredentials] = useState<SessionCredentials | null>(null);
  const [session, setSession] = useState<VerificationSession | null>(null);
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [selectedDocumentType, setSelectedDocumentType] = useState("");
  const [consented, setConsented] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deviceReady, setDeviceReady] = useState(false);
  const [continueOnDevice, setContinueOnDevice] = useState(Boolean(handoff));
  const [handoffUrl, setHandoffUrl] = useState("");
  const [handoffBusy, setHandoffBusy] = useState(false);

  const load = useCallback(async (nextCredentials: SessionCredentials) => {
    const [nextSession, nextStatus] = await Promise.all([
      fetchVerificationSession(nextCredentials),
      fetchVerificationStatus(nextCredentials),
    ]);
    setSession(nextSession);
    setSelectedDocumentType(
      (current) => current || nextSession.document.document_type,
    );
    setStatus(nextStatus);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(async () => {
      try {
        let nextCredentials: SessionCredentials | null;
        if (handoff) {
          nextCredentials = await redeemMobileHandoff(handoff);
          if (!cancelled) {
            window.history.replaceState(
              null,
              "",
              `/verify/${nextCredentials.sessionId}`,
            );
          }
        } else {
          nextCredentials = consumeSessionCredentials(sessionId);
        }

        if (!nextCredentials) {
          throw new Error(
            "This secure verification link is missing its session credential. Request a new link from the organization.",
          );
        }
        if (cancelled) return;
        setCredentials(nextCredentials);
        await load(nextCredentials);
        const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(
          navigator.userAgent,
        );
        setContinueOnDevice(Boolean(handoff) || isMobile);
      } catch (caught) {
        if (!cancelled) setError(messageOf(caught));
      } finally {
        if (!cancelled) setDeviceReady(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [handoff, load, sessionId]);

  useEffect(() => {
    if (!credentials || !status || !PROCESSING_STEPS.has(status.current_step)) {
      return;
    }
    const timer = window.setInterval(() => {
      void fetchVerificationStatus(credentials)
        .then((next) => {
          setStatus(next);
          setError(null);
        })
        .catch((caught) => setError(messageOf(caught)));
    }, 3500);
    return () => window.clearInterval(timer);
  }, [credentials, status]);

  useEffect(() => {
    if (!handoffUrl || !credentials || continueOnDevice) return;
    const timer = window.setInterval(() => {
      void fetchVerificationStatus(credentials)
        .then((next) => {
          setStatus(next);
          if (
            ["completed", "failed", "expired", "cancelled"].includes(
              next.current_step,
            )
          ) {
            setContinueOnDevice(true);
          }
        })
        .catch((caught) => setError(messageOf(caught)));
    }, 3000);
    return () => window.clearInterval(timer);
  }, [continueOnDevice, credentials, handoffUrl]);

  async function run(action: () => Promise<unknown>) {
    if (!credentials || busy) return;
    setBusy(true);
    setError(null);
    try {
      await action();
      setFile(null);
      await load(credentials);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy(false);
    }
  }

  function selectEvidence(nextFile: File) {
    const supportedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
    if (!supportedTypes.has(nextFile.type.toLowerCase())) {
      setFile(null);
      setError("Choose a JPEG, PNG, or WebP image.");
      return;
    }
    if (nextFile.size > MAX_IMAGE_BYTES) {
      setFile(null);
      setError("The image must be 10 MB or smaller.");
      return;
    }
    if (nextFile.size === 0) {
      setFile(null);
      setError("The selected image is empty. Choose another image.");
      return;
    }
    setError(null);
    setFile(nextFile);
  }

  async function startMobileHandoff() {
    if (!credentials || handoffBusy) return;
    setHandoffBusy(true);
    setError(null);
    try {
      const result = await createMobileHandoff(credentials);
      setHandoffUrl(result.handoff_url);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setHandoffBusy(false);
    }
  }

  if (!deviceReady) {
    return <OpeningState title="Opening your secure session" />;
  }
  if (error && (!credentials || !session || !status)) {
    return <OpeningState title="Verification unavailable" message={error} />;
  }
  if (!credentials || !session || !status) {
    return <OpeningState title="Opening your secure session" />;
  }

  if (!continueOnDevice) {
    return (
      <MobileHandoff
        organizationName={session.organization.name}
        handoffUrl={handoffUrl}
        busy={handoffBusy}
        error={error}
        onCreate={startMobileHandoff}
        onContinue={() => setContinueOnDevice(true)}
      />
    );
  }

  const step = status.current_step;
  const availableDocuments =
    session.available_documents?.length
      ? session.available_documents
      : [session.document];
  const selectedDocument =
    availableDocuments.find(
      (document) => document.document_type === selectedDocumentType,
    ) ?? session.document;
  const finish = () => {
    clearSessionCredentials(credentials.sessionId);
    const returnUrl =
      session.redirect_url ||
      process.env.NEXT_PUBLIC_ONBOARDING_RETURN_URL ||
      "http://localhost:3001/onboarding";
    window.location.assign(returnUrl);
  };

  return (
    <VerificationFrame
      organizationName={session.organization.name}
      organizationLogoUrl={session.organization.logo_url}
      purpose={session.purpose}
      currentStep={step}
      reference={status.verification_id}
    >
      {error ? (
        <div role="alert" className="mb-4 rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {step === "consent" ? (
        <StepCard
          eyebrow="Step 1 of 5"
          title="Review and give consent"
          description="Understand what will be processed before you continue. You remain in control of whether to proceed."
        >
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              [FileText, "Identity document", "Used to read and validate identity details"],
              [ScanFace, "Live selfie", "Compared with the portrait on your document"],
              [ShieldCheck, "Security signals", "Used for liveness, fraud risk, and audit"],
            ].map(([Icon, title, detail]) => {
              const ItemIcon = Icon as typeof FileText;
              return (
                <div key={String(title)} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                  <ItemIcon className="h-5 w-5 text-blue-600" aria-hidden="true" />
                  <p className="mt-3 text-sm font-semibold text-slate-900">{String(title)}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{String(detail)}</p>
                </div>
              );
            })}
          </div>
          <label className="flex cursor-pointer gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-blue-300 hover:bg-blue-50/30">
            <input
              type="checkbox"
              checked={consented}
              onChange={(event) => setConsented(event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-slate-300 accent-blue-600"
            />
            <span className="text-sm leading-6 text-slate-600">
              I consent to {session.organization.name} using IdentityCore to
              process my document, selfie, biometric evidence, and security
              metadata for <strong className="font-medium text-slate-900">{session.purpose}</strong>.
            </span>
          </label>
          <div className="flex items-center justify-between gap-4 border-t border-slate-100 pt-5">
            <p className="flex items-center gap-2 text-xs text-slate-400">
              <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
              Consent is recorded in the audit trail
            </p>
            <Button
              disabled={!consented || busy}
              onClick={() => run(() => acceptConsent(credentials))}
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Accept and continue
            </Button>
          </div>
        </StepCard>
      ) : null}

      {step === "document_capture" ? (
        <StepCard
          eyebrow="Step 2 of 5"
          title={`Capture your ${selectedDocument.label}`}
          description="Choose the identity document you want to use, then capture the original physical document with all four edges visible."
        >
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-800">
              Document type
            </span>
            <select
              value={selectedDocumentType}
              onChange={(event) => {
                setSelectedDocumentType(event.target.value);
                setFile(null);
                setError(null);
              }}
              disabled={busy}
              className="h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              {availableDocuments.map((document) => (
                <option
                  key={document.document_type}
                  value={document.document_type}
                >
                  {document.label}
                </option>
              ))}
            </select>
          </label>
          {file ? (
            <EvidenceReview file={file} onRetake={() => setFile(null)} />
          ) : (
            <CameraCapture
              facingMode="environment"
              label={`${selectedDocument.label} camera`}
              onCapture={selectEvidence}
            />
          )}
          <div className="flex justify-end border-t border-slate-100 pt-5">
            <Button
              disabled={!file || busy}
              onClick={() =>
                run(async () => {
                  if (!file) return;
                  const uploadId = await createUpload(
                    credentials,
                    "document_capture",
                    file,
                  );
                  await submitDocument(credentials, {
                    documentType: selectedDocument.document_type,
                    countryCode: session.document.country_code,
                    uploadId,
                  });
                })
              }
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Submit document
            </Button>
          </div>
        </StepCard>
      ) : null}

      {step === "document_processing" ? (
        <StepCard
          eyebrow="Secure document check"
          title={`Checking your ${session.document.label}`}
          description="IdentityCore is checking capture quality and reading the supported document evidence."
        >
          <ProcessingPanel
            title="Document processing in progress"
            items={["Capture quality", "Document type", "OCR evidence", "Review signals"]}
          />
        </StepCard>
      ) : null}

      {step === "selfie_capture" ? (
        <StepCard
          eyebrow="Step 3 of 5"
          title="Take a live selfie"
          description="Remove hats or dark glasses, face the camera directly, and use even lighting. Your selfie will be compared with the document portrait."
        >
          {file ? (
            <EvidenceReview file={file} onRetake={() => setFile(null)} />
          ) : (
            <CameraCapture
              facingMode="user"
              label="Live selfie camera"
              onCapture={selectEvidence}
            />
          )}
          <div className="flex justify-end border-t border-slate-100 pt-5">
            <Button
              disabled={!file || busy}
              onClick={() =>
                run(async () => {
                  if (!file) return;
                  const uploadId = await createUpload(
                    credentials,
                    "selfie_capture",
                    file,
                  );
                  await submitSelfie(credentials, uploadId);
                })
              }
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Submit selfie
            </Button>
          </div>
        </StepCard>
      ) : null}

      {step === "liveness_check" ? (
        <StepCard
          eyebrow="Step 4 of 5"
          title="Confirm you are present"
          description="A passive liveness check evaluates the live selfie for presence signals. It does not search for your face in an identity database."
        >
          <div className="rounded-3xl border border-blue-100 bg-blue-50/60 p-6 text-center">
            <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white text-blue-700 shadow-sm">
              <ScanFace className="h-8 w-8" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-base font-semibold text-slate-950">Ready for the presence check</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
              This uses the selfie you just reviewed. No additional gesture is required.
            </p>
            <Button
              className="mt-5"
              disabled={!status.evidence.selfie_capture_id || busy}
              onClick={() =>
                run(() =>
                  submitLiveness(
                    credentials,
                    status.evidence.selfie_capture_id,
                  ),
                )
              }
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanFace className="h-4 w-4" />}
              Start presence check
            </Button>
          </div>
        </StepCard>
      ) : null}

      {step === "processing" ? (
        <StepCard
          eyebrow="Step 5 of 5"
          title="Completing your verification"
          description="The submitted evidence is being evaluated against the requesting organization’s verification policy."
        >
          <ProcessingPanel
            title="Secure decision processing"
            items={["Liveness result", "Face comparison", "Risk rules", "Final decision"]}
          />
        </StepCard>
      ) : null}

      {step === "completed" ? (
        <TerminalPanel
          state={status.status === "verified" ? "verified" : "review"}
          message={status.message}
          onFinish={finish}
        />
      ) : null}
      {step === "failed" ? (
        <TerminalPanel state="failed" message={status.message} onFinish={finish} />
      ) : null}
      {step === "expired" ? (
        <TerminalPanel state="expired" message={status.message} />
      ) : null}
      {step === "cancelled" ? (
        <TerminalPanel state="cancelled" message={status.message} />
      ) : null}

      {busy ? (
        <p aria-live="polite" className="mt-4 flex items-center justify-end gap-2 text-xs text-slate-500">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Submitting securely…
        </p>
      ) : null}
    </VerificationFrame>
  );
}

function MobileHandoff({
  organizationName,
  handoffUrl,
  busy,
  error,
  onCreate,
  onContinue,
}: {
  organizationName: string;
  handoffUrl: string;
  busy: boolean;
  error: string | null;
  onCreate: () => void;
  onContinue: () => void;
}) {
  return (
    <main id="main-content" className="verification-page flex min-h-screen items-center px-4 py-10">
      <Card className="mx-auto w-full max-w-xl overflow-hidden rounded-[2rem] border-slate-200 bg-white shadow-2xl shadow-slate-300/40">
        <CardHeader className="border-b border-slate-100 px-6 py-7 sm:px-8">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
            <Smartphone className="h-6 w-6" aria-hidden="true" />
          </span>
          <CardTitle className="mt-4 text-2xl tracking-tight">Continue securely on your phone</CardTitle>
          <p className="text-sm leading-6 text-slate-500">
            {organizationName} requested this verification. A phone camera usually gives clearer document and selfie captures.
          </p>
        </CardHeader>
        <CardContent className="space-y-5 px-6 py-7 sm:px-8">
          {error ? <p role="alert" className="rounded-2xl bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          {handoffUrl ? (
            <div className="space-y-4 text-center">
              <div className="mx-auto w-fit rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <QRCodeSVG value={handoffUrl} size={220} level="M" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">Scan with your phone camera</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">The one-time code expires shortly and cannot be reused.</p>
              </div>
              <Button variant="outline" onClick={() => navigator.clipboard.writeText(handoffUrl)}>
                <Copy className="h-4 w-4" />
                Copy mobile link
              </Button>
              <p className="flex items-center justify-center gap-2 text-xs text-slate-400">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Waiting for completion on your phone
              </p>
            </div>
          ) : (
            <Button className="w-full" onClick={onCreate} disabled={busy}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Smartphone className="h-4 w-4" />}
              Show secure QR code
            </Button>
          )}
          <div className="relative py-1 text-center text-xs text-slate-400 before:absolute before:left-0 before:right-0 before:top-1/2 before:h-px before:bg-slate-100">
            <span className="relative bg-white px-3">or</span>
          </div>
          <Button variant="outline" className="w-full" onClick={onContinue}>
            <Monitor className="h-4 w-4" />
            Continue on this computer
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}

function OpeningState({
  title,
  message,
}: {
  title: string;
  message?: string;
}) {
  return (
    <main id="main-content" className="verification-page flex min-h-screen items-center px-4 py-10">
      <Card className="mx-auto w-full max-w-md rounded-[2rem] border-slate-200 bg-white shadow-xl shadow-slate-200/50">
        <CardContent className="flex min-h-64 flex-col items-center justify-center gap-3 p-8 text-center">
          {!message ? <Loader2 className="h-7 w-7 animate-spin text-blue-600" /> : <ShieldCheck className="h-8 w-8 text-slate-400" />}
          <h1 className="text-xl font-semibold tracking-tight text-slate-950">{title}</h1>
          {message ? <p className="text-sm leading-6 text-slate-500">{message}</p> : <p className="text-sm text-slate-500">Validating your one-time session credential…</p>}
        </CardContent>
      </Card>
    </main>
  );
}

function messageOf(error: unknown) {
  const message = error instanceof Error ? error.message : "";
  return /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror|failed to fetch|networkerror/i.test(message)
    ? "The verification service is temporarily unavailable. Check your connection and try again."
    : message || "Something went wrong. Please try again.";
}
