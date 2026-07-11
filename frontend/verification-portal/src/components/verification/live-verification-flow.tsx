"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Copy, Loader2, Monitor, ShieldCheck, Smartphone } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { Button, Card, CardContent, CardHeader, CardTitle, Progress } from "@identitycore/ui";
import { CameraCapture } from "./camera-capture";
import {
  acceptConsent,
  clearSessionCredentials,
  consumeSessionCredentials,
  createUpload,
  fetchVerificationSession,
  fetchVerificationStatus,
  submitDocument,
  submitLiveness,
  submitSelfie,
  type SessionCredentials,
  type VerificationSession,
  type VerificationStatus,
  createMobileHandoff,
  redeemMobileHandoff,
} from "@/lib/session-api";

const STEPS = ["consent", "document_capture", "document_processing", "selfie_capture", "liveness_check", "processing", "completed", "failed"];

export function LiveVerificationFlow({ sessionId, handoff }: { sessionId: string; handoff?: string }) {
  const [credentials, setCredentials] = useState<SessionCredentials | null>(null);
  const [session, setSession] = useState<VerificationSession | null>(null);
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [consented, setConsented] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deviceReady, setDeviceReady] = useState(false);
  const [continueOnDesktop, setContinueOnDesktop] = useState(Boolean(handoff));
  const [handoffUrl, setHandoffUrl] = useState("");
  const [handoffBusy, setHandoffBusy] = useState(false);

  const load = useCallback(async (nextCredentials: SessionCredentials) => {
    const [nextSession, nextStatus] = await Promise.all([
      fetchVerificationSession(nextCredentials),
      fetchVerificationStatus(nextCredentials),
    ]);
    setSession(nextSession);
    setStatus(nextStatus);
  }, []);

  useEffect(() => {
    void Promise.resolve().then(async () => {
      if (handoff) {
        try {
          const mobileCredentials = await redeemMobileHandoff(handoff);
          setCredentials(mobileCredentials);
          window.history.replaceState(null, "", `/verify/${mobileCredentials.sessionId}`);
          await load(mobileCredentials);
        } catch (caught) {
          setError(messageOf(caught));
        } finally {
          setDeviceReady(true);
        }
        return;
      }
      const nextCredentials = consumeSessionCredentials(sessionId);
      if (!nextCredentials) {
        setError("This secure verification link is missing its session credential.");
        return;
      }
      setCredentials(nextCredentials);
      await load(nextCredentials).catch((caught) => setError(messageOf(caught)));
      const mobileDevice = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
      setContinueOnDesktop(mobileDevice);
      setDeviceReady(true);
    });
  }, [handoff, load, sessionId]);

  useEffect(() => {
    if (!handoffUrl || !credentials) return;
    const timer = window.setInterval(() => {
      void fetchVerificationStatus(credentials).then((next) => {
        setStatus(next);
        if (["completed", "failed", "expired"].includes(next.current_step)) {
          setContinueOnDesktop(true);
          window.clearInterval(timer);
        }
      });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [credentials, handoffUrl]);

  useEffect(() => {
    if (!credentials || !status || !["document_processing", "processing"].includes(status.current_step)) return;
    const timer = window.setInterval(() => {
      void fetchVerificationStatus(credentials).then(setStatus).catch(() => window.clearInterval(timer));
    }, 4000);
    return () => window.clearInterval(timer);
  }, [credentials, status]);

  async function run(action: () => Promise<unknown>) {
    if (!credentials) return;
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
      setError("Choose a JPEG, PNG, or WebP image. PDF and other document files are not accepted for identity capture.");
      return;
    }
    setError(null);
    setFile(nextFile);
  }

  if (error && !session) return <StateCard title="Verification unavailable" message={error} />;
  if (!deviceReady || !credentials || !session || !status) return <StateCard title="Opening secure session" loading />;

  async function startMobileHandoff() {
    if (!credentials) return;
    setHandoffBusy(true); setError(null);
    try { const result = await createMobileHandoff(credentials); setHandoffUrl(result.handoff_url); }
    catch (caught) { setError(messageOf(caught)); }
    finally { setHandoffBusy(false); }
  }

  if (!continueOnDesktop) {
    return <main className="flex min-h-screen items-center px-4 py-8"><Card className="mx-auto w-full max-w-xl rounded-3xl"><CardHeader><div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><Smartphone /></div><CardTitle>Complete verification on your phone</CardTitle></CardHeader><CardContent className="space-y-5"><p className="text-sm leading-6 text-slate-600">A phone usually gives better document focus, selfie quality, and liveness results.</p>{error ? <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}{handoffUrl ? <div className="space-y-4 text-center"><div className="mx-auto w-fit rounded-2xl border bg-white p-4"><QRCodeSVG value={handoffUrl} size={220} level="M" /></div><p className="text-sm text-slate-600">Scan once with your phone. This code expires shortly and cannot be reused.</p><Button variant="outline" onClick={() => navigator.clipboard.writeText(handoffUrl)}><Copy className="h-4 w-4" />Copy mobile link</Button><p className="text-xs text-slate-500">This page will update automatically when mobile verification finishes.</p></div> : <Button className="w-full" onClick={startMobileHandoff} disabled={handoffBusy}>{handoffBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Smartphone className="h-4 w-4" />}Show mobile QR code</Button>}<Button variant="outline" className="w-full" onClick={() => setContinueOnDesktop(true)}><Monitor className="h-4 w-4" />Continue on this computer</Button></CardContent></Card></main>;
  }

  const step = status.current_step;
  const index = Math.max(0, STEPS.indexOf(step));
  const returnUrl = process.env.NEXT_PUBLIC_ONBOARDING_RETURN_URL ?? "http://localhost:3001/onboarding";

  return (
    <main id="main-content" className="flex min-h-screen items-center px-4 py-8 sm:px-6">
    <div className="mx-auto w-full max-w-2xl space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div><p className="text-sm text-slate-500">Requested by</p><h1 className="text-xl font-semibold">{session.organization.name}</h1></div>
        <ShieldCheck className="h-7 w-7 text-blue-600" />
      </div>
      <Progress value={((index + 1) / STEPS.length) * 100} />
      <Card className="rounded-3xl border-slate-200 shadow-sm">
        <CardHeader><CardTitle>{titleFor(step, session.document.label)}</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <p className="text-sm leading-6 text-slate-600">
            {step === "document_capture" && file
              ? busy
                ? `Submitting your ${session.document.label} securely…`
                : `Review your new ${session.document.label} image, then submit it for verification.`
              : status.message}
          </p>
          {error ? <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

          {step === "consent" ? <>
            <label className="flex gap-3 rounded-2xl border p-4 text-sm leading-6">
              <input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />
              I consent to the processing of my identity document, selfie, and biometric verification evidence.
            </label>
            <Button disabled={!consented || busy} onClick={() => run(() => acceptConsent(credentials))}>Accept and continue</Button>
          </> : null}

          {step === "document_capture" ? <>
            {!file ? <CameraCapture facingMode="environment" label="Identity document camera" onCapture={selectEvidence} /> : <EvidenceReview file={file} onRetake={() => setFile(null)} />}
            <Button disabled={!file || busy} onClick={() => run(async () => {
              if (!file) return;
              const uploadId = await createUpload(credentials, "document_capture", file);
              await submitDocument(credentials, {
                documentType: session.document.document_type,
                countryCode: session.document.country_code,
                uploadId,
              });
            })}>Submit document</Button>
          </> : null}

          {step === "document_processing" ? <div className="flex items-center gap-3 rounded-2xl bg-blue-50 p-4 text-sm text-blue-800"><Loader2 className="h-5 w-5 animate-spin" />Checking document type, readability, and image quality before selfie capture.</div> : null}

          {step === "selfie_capture" ? <>
            {!file ? <CameraCapture facingMode="user" label="Selfie camera" onCapture={selectEvidence} /> : <EvidenceReview file={file} onRetake={() => setFile(null)} />}
            <Button disabled={!file || busy} onClick={() => run(async () => {
              if (!file) return;
              const uploadId = await createUpload(credentials, "selfie_capture", file);
              const selfie = await submitSelfie(credentials, uploadId);
              await submitLiveness(credentials, selfie.selfie_capture_id);
            })}>Submit selfie and check liveness</Button>
          </> : null}

          {step === "liveness_check" ? <div className="space-y-4"><p className="text-sm leading-6 text-slate-600">Passive liveness uses your submitted selfie. No additional photo or gesture is required.</p><Button disabled={!status.evidence.selfie_capture_id || busy} onClick={() => run(() => submitLiveness(credentials, status.evidence.selfie_capture_id))}>Start liveness check</Button></div> : null}

          {step === "processing" ? <div className="flex items-center gap-3 rounded-2xl bg-blue-50 p-4 text-sm text-blue-800"><Loader2 className="h-5 w-5 animate-spin" />Document and biometric evidence are being processed.</div> : null}

          {step === "completed" ? <div className="space-y-4"><div className="flex items-center gap-3 text-emerald-700"><CheckCircle2 className="h-6 w-6" />{status.status === "verified" ? "Verification completed successfully." : "Verification completed and requires review."}</div><Button onClick={() => { clearSessionCredentials(sessionId); window.location.assign(returnUrl); }}>Return to onboarding</Button></div> : null}
          {step === "failed" ? <div className="space-y-4"><p role="alert" className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">We could not complete the automated verification. Please return to onboarding for the next available step.</p><Button onClick={() => { clearSessionCredentials(sessionId); window.location.assign(returnUrl); }}>Return to onboarding</Button></div> : null}
          {busy ? <div aria-live="polite" className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />Submitting securely…</div> : null}
        </CardContent>
      </Card>
    </div>
    </main>
  );
}

function EvidenceReview({ file, onRetake }: { file: File; onRetake: () => void }) {
  const [url, setUrl] = useState("");
  const [previewFailed, setPreviewFailed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    const reader = new FileReader();
    setUrl("");
    setPreviewFailed(false);
    reader.onload = () => {
      if (!cancelled && typeof reader.result === "string") {
        setUrl(reader.result);
      }
    };
    reader.onerror = () => {
      if (!cancelled) setPreviewFailed(true);
    };
    reader.readAsDataURL(file);
    return () => {
      cancelled = true;
      reader.abort();
    };
  }, [file]);
  return <div className="space-y-3">
    {previewFailed ? (
      <p className="rounded-2xl bg-amber-50 p-4 text-sm text-amber-800">
        This image cannot be previewed. Retake it or choose a JPEG, PNG, or WebP file.
      </p>
    ) : url ? (
      /* eslint-disable-next-line @next/next/no-img-element */
      <img src={url} onError={() => setPreviewFailed(true)} alt="Captured evidence preview" className="max-h-96 w-full rounded-2xl bg-slate-950 object-contain" />
    ) : <div className="flex min-h-48 items-center justify-center rounded-2xl bg-slate-950 text-sm text-slate-300"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Preparing preview…</div>}
    <Button variant="outline" onClick={onRetake}>Retake</Button>
  </div>;
}

function StateCard({ title, message, loading = false }: { title: string; message?: string; loading?: boolean }) {
  return <Card className="mx-auto max-w-lg rounded-3xl"><CardContent className="flex min-h-48 flex-col items-center justify-center gap-3 p-8 text-center">{loading ? <Loader2 className="h-6 w-6 animate-spin" /> : null}<h1 className="text-xl font-semibold">{title}</h1>{message ? <p className="text-sm text-slate-600">{message}</p> : null}</CardContent></Card>;
}

function messageOf(error: unknown) {
  const message = error instanceof Error ? error.message : "";
  return /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror|failed to fetch|networkerror/i.test(message)
    ? "The verification service is temporarily unavailable. Please try again shortly."
    : message || "Something went wrong. Please try again.";
}
function titleFor(step: string, documentLabel: string) { return ({ consent: "Review and consent", document_capture: "Let’s verify your identity", document_processing: `Checking your ${documentLabel}`, selfie_capture: "Take a live selfie", liveness_check: "Confirm you’re present", processing: "Completing your verification", completed: "Verification complete", failed: "Verification needs attention", expired: "Session expired" } as Record<string, string>)[step] ?? "Identity verification"; }
