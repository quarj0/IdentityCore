"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Fingerprint,
  Loader2,
  ShieldCheck,
  UserCircle2,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Progress,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import { submitAdministratorIdentityVerification } from "@/lib/onboarding-api";
import { fetchPublicCatalog } from "@/lib/public-graphql";
import {
  acceptVerificationConsent,
  createSessionUpload,
  fetchVerificationDetail,
  fetchVerificationSession,
  fetchVerificationStatus,
  submitVerificationDocument,
  submitVerificationLiveness,
  submitVerificationSelfie,
  type SessionCredentials,
  type VerificationDetailResponse,
  type VerificationSessionSummary,
  type VerificationStatusResponse,
} from "@/lib/verification-api";

const STEPS = ["Consent", "Document", "Selfie", "Liveness", "Result"];
const WORKSPACE_DASHBOARD_ORIGIN =
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export function VerificationSessionFlow({
  sessionId = "",
  sessionToken = "",
  verificationId = "",
}: {
  sessionId?: string;
  sessionToken?: string;
  verificationId?: string;
}) {
  const credentials = useMemo<SessionCredentials | null>(() => {
    if (!sessionId || !sessionToken) {
      return null;
    }

    return { sessionId, sessionToken };
  }, [sessionId, sessionToken]);

  const [submitting, setSubmitting] = useState(false);
  const [session, setSession] = useState<VerificationSessionSummary | null>(
    null,
  );
  const [status, setStatus] = useState<VerificationStatusResponse | null>(null);
  const [detail, setDetail] = useState<VerificationDetailResponse | null>(null);
  const [documentTypes, setDocumentTypes] = useState<
    Array<{ code: string; name: string }>
  >([]);
  const [countryProfiles, setCountryProfiles] = useState<
    Array<{
      code: string;
      name: string;
      supportedDocumentTypes: Array<{
        documentType: string;
        localName: string;
      }>;
    }>
  >([]);
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [documentType, setDocumentType] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [documentFront, setDocumentFront] = useState<File | null>(null);
  const [documentBack, setDocumentBack] = useState<File | null>(null);
  const [selfieFile, setSelfieFile] = useState<File | null>(null);
  const [selfieCaptureId, setSelfieCaptureId] = useState("");
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [onboardingSubmitted, setOnboardingSubmitted] = useState(false);
  const [feedback, setFeedback] = useState<{
    kind: "error" | "success";
    title: string;
    message: string;
  } | null>(null);
  const loading =
    credentials !== null &&
    !catalogError &&
    (!session ||
      !status ||
      documentTypes.length === 0 ||
      countryProfiles.length === 0);

  useEffect(() => {
    if (!credentials) {
      return;
    }

    Promise.all([
      fetchVerificationSession(credentials),
      fetchVerificationStatus(credentials),
      fetchPublicCatalog(),
      verificationId
        ? fetchVerificationDetail(verificationId).catch(() => null)
        : Promise.resolve(null),
    ])
      .then(
        ([sessionPayload, statusPayload, catalogPayload, detailPayload]) => {
          setSession(sessionPayload);
          setStatus(statusPayload);
          setCountryProfiles(catalogPayload.countryProfiles);
          setDocumentTypes(catalogPayload.documentTypes);
          setCountryCode(catalogPayload.countryProfiles[0]?.code ?? "");
          setDetail(detailPayload);
        },
      )
      .catch((error) => {
        const message = getErrorMessage(error);
        setCatalogError(message);
        setFeedback({
          kind: "error",
          title: "Unable to load verification session",
          message,
        });
      });
  }, [credentials, verificationId]);

  useEffect(() => {
    if (!credentials || !onboardingSubmitted) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const nextStatus = await fetchVerificationStatus(credentials);
        setStatus(nextStatus);
        if (verificationId) {
          const nextDetail = await fetchVerificationDetail(verificationId);
          setDetail(nextDetail);
        }
      } catch {
        window.clearInterval(interval);
      }
    }, 4000);

    return () => window.clearInterval(interval);
  }, [credentials, onboardingSubmitted, verificationId]);

  const currentStepIndex = getStepIndex(status?.current_step ?? "consent");
  const progress = ((currentStepIndex + 1) / STEPS.length) * 100;
  const supportedDocumentTypes =
    countryProfiles.find((item) => item.code === countryCode)
      ?.supportedDocumentTypes ?? [];

  async function handleConsent() {
    if (!credentials) {
      return;
    }

    setSubmitting(true);
    setFeedback(null);
    try {
      await acceptVerificationConsent(credentials, consentAccepted);
      const nextStatus = await fetchVerificationStatus(credentials);
      setStatus(nextStatus);
      setFeedback({
        kind: "success",
        title: "Consent recorded",
        message: "You can continue with document capture.",
      });
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to submit consent",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDocumentSubmit() {
    if (!credentials || !documentFront || !documentType) {
      return;
    }

    setSubmitting(true);
    setFeedback(null);
    try {
      const frontUpload = await createSessionUpload(
        credentials,
        "document_capture",
        documentFront,
      );
      const captures: Array<{ side: string; upload_id: string }> = [
        { side: "front", upload_id: frontUpload.upload_id },
      ];

      if (documentBack) {
        const backUpload = await createSessionUpload(
          credentials,
          "document_capture",
          documentBack,
        );
        captures.push({ side: "back", upload_id: backUpload.upload_id });
      }

      await submitVerificationDocument(credentials, {
        documentType,
        countryCode,
        captures,
      });

      const nextStatus = await fetchVerificationStatus(credentials);
      setStatus(nextStatus);
      setFeedback({
        kind: "success",
        title: "Document submitted",
        message: "Continue with the selfie capture step.",
      });
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to submit document",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSelfieSubmit() {
    if (!credentials || !selfieFile) {
      return;
    }

    setSubmitting(true);
    setFeedback(null);
    try {
      const upload = await createSessionUpload(
        credentials,
        "selfie_capture",
        selfieFile,
      );
      const payload = await submitVerificationSelfie(credentials, {
        captureType: "image",
        uploadId: upload.upload_id,
      });
      setSelfieCaptureId(payload.selfie_capture_id);
      const nextStatus = await fetchVerificationStatus(credentials);
      setStatus(nextStatus);
      setFeedback({
        kind: "success",
        title: "Selfie submitted",
        message: "Continue with the liveness confirmation.",
      });
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to submit selfie",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLivenessSubmit() {
    if (!credentials || !selfieCaptureId || !verificationId) {
      return;
    }

    setSubmitting(true);
    setFeedback(null);
    try {
      await submitVerificationLiveness(credentials, {
        livenessType: "passive",
        selfieCaptureId,
      });
      await submitAdministratorIdentityVerification(verificationId);
      setOnboardingSubmitted(true);
      window.location.assign(WORKSPACE_DASHBOARD_ORIGIN.replace(/\/$/, ""));
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to submit liveness confirmation",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (!credentials) {
    return (
      <VerificationError message="A session ID and token are required to open this verification flow." />
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (catalogError) {
    return <VerificationError message={catalogError} />;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.72fr_0.28fr]">
      <Card className="rounded-4xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>{STEPS[currentStepIndex]}</CardTitle>
              <CardDescription>
                {session?.organization.name} verification for {session?.purpose}
                .
              </CardDescription>
            </div>

            <Badge variant="secondary" className="rounded-full">
              Step {currentStepIndex + 1} of {STEPS.length}
            </Badge>
          </div>

          <Progress value={progress} className="mt-5" />
        </CardHeader>

        <CardContent className="space-y-6">
          {feedback ? (
            <InlineStatus
              kind={feedback.kind}
              title={feedback.title}
              message={feedback.message}
            />
          ) : null}

          {currentStepIndex === 0 ? (
            <StepCard
              icon={<ShieldCheck className="h-6 w-6" />}
              title="Consent to administrator verification"
              description="Confirm that IdentityCore may process your identity evidence for workspace onboarding."
            >
              <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={consentAccepted}
                  onChange={(event) => setConsentAccepted(event.target.checked)}
                />
                <span className="text-sm leading-6 text-muted-foreground">
                  I consent to IdentityCore processing my administrator identity
                  evidence for workspace onboarding and production approval.
                </span>
              </label>

              <Button
                onClick={handleConsent}
                disabled={!consentAccepted || submitting}
                className="rounded-xl"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Accept and continue
              </Button>
            </StepCard>
          ) : null}

          {currentStepIndex === 1 ? (
            <StepCard
              icon={<FileText className="h-6 w-6" />}
              title="Submit your identity document"
              description="Upload a supported document image. Front image is required and back image is optional."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Country</Label>
                  <Select value={countryCode} onValueChange={setCountryCode}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select country" />
                    </SelectTrigger>
                    <SelectContent>
                      {countryProfiles.map((profile) => (
                        <SelectItem key={profile.code} value={profile.code}>
                          {profile.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Document type</Label>
                  <Select value={documentType} onValueChange={setDocumentType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select document type" />
                    </SelectTrigger>
                    <SelectContent>
                      {(supportedDocumentTypes.length
                        ? supportedDocumentTypes.map((item) => ({
                            code: item.documentType,
                            name: item.localName,
                          }))
                        : documentTypes
                      ).map((item) => (
                        <SelectItem key={item.code} value={item.code}>
                          {item.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="documentFront">Front image</Label>
                  <Input
                    id="documentFront"
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) =>
                      setDocumentFront(event.target.files?.[0] ?? null)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="documentBack">Back image</Label>
                  <Input
                    id="documentBack"
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) =>
                      setDocumentBack(event.target.files?.[0] ?? null)
                    }
                  />
                </div>
              </div>

              <Button
                onClick={handleDocumentSubmit}
                disabled={!documentType || !documentFront || submitting}
                className="rounded-xl"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Submit document
              </Button>
            </StepCard>
          ) : null}

          {currentStepIndex === 2 ? (
            <StepCard
              icon={<UserCircle2 className="h-6 w-6" />}
              title="Submit your selfie"
              description="Upload a clear selfie of the same person shown on the document."
            >
              <div className="space-y-2">
                <Label htmlFor="selfieFile">Selfie image</Label>
                <Input
                  id="selfieFile"
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) =>
                    setSelfieFile(event.target.files?.[0] ?? null)
                  }
                />
              </div>

              <Button
                onClick={handleSelfieSubmit}
                disabled={!selfieFile || submitting}
                className="rounded-xl"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Submit selfie
              </Button>
            </StepCard>
          ) : null}

          {currentStepIndex === 3 ? (
            <StepCard
              icon={<Fingerprint className="h-6 w-6" />}
              title="Confirm liveness"
              description="Submit the passive liveness check linked to your selfie capture."
            >
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted-foreground">
                This flow uses the backend passive liveness step and submits it
                against the selfie capture you just uploaded.
              </div>

              <Button
                onClick={handleLivenessSubmit}
                disabled={!selfieCaptureId || submitting}
                className="rounded-xl"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Submit liveness
              </Button>
            </StepCard>
          ) : null}

          {currentStepIndex >= 4 ? (
            <StepCard
              icon={<CheckCircle2 className="h-6 w-6" />}
              title="Verification result"
              description={
                status?.message ??
                "Your verification status is available below."
              }
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <ResultItem
                  label="Verification status"
                  value={detail?.status ?? status?.status ?? "unknown"}
                />
                <ResultItem
                  label="Face match"
                  value={detail?.checks.face_match.status ?? "pending"}
                />
                <ResultItem
                  label="Liveness"
                  value={detail?.checks.liveness.status ?? "pending"}
                />
                <ResultItem
                  label="Decision"
                  value={detail?.decision?.decision ?? "Awaiting decision"}
                />
              </div>

              {detail?.decision?.reason_detail ? (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted-foreground">
                  {detail.decision.reason_detail}
                </div>
              ) : null}

              {detail?.evidence_report?.pdf_download_url ? (
                <Button asChild variant="outline" className="rounded-xl">
                  <a
                    href={detail.evidence_report.pdf_download_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open evidence report
                  </a>
                </Button>
              ) : null}
            </StepCard>
          ) : null}
        </CardContent>
      </Card>

      <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <CardTitle>Verification progress</CardTitle>
          <CardDescription>
            Session `{session?.session_id}` expires at{" "}
            {session?.expires_at ?? "unknown"}.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3">
          {STEPS.map((item, index) => (
            <div
              key={item}
              className={
                index === currentStepIndex
                  ? "flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-3"
                  : index < currentStepIndex
                    ? "flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3"
                    : "flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3"
              }
            >
              <div
                className={
                  index <= currentStepIndex
                    ? "flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white"
                    : "flex h-8 w-8 items-center justify-center rounded-xl bg-white text-slate-600 ring-1 ring-slate-200"
                }
              >
                {index < currentStepIndex ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <span className="text-xs font-semibold">{index + 1}</span>
                )}
              </div>
              <p className="text-sm font-medium">{item}</p>
            </div>
          ))}

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted-foreground">
            Backend status: {status?.status ?? "unknown"}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StepCard({
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

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function VerificationError({ message }: { message: string }) {
  return (
    <Card className="rounded-3xl border-red-200 bg-red-50 shadow-sm">
      <CardHeader>
        <div className="flex items-center gap-3 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <CardTitle>Verification unavailable</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-red-700">{message}</p>
      </CardContent>
    </Card>
  );
}

function getStepIndex(step: string) {
  switch (step) {
    case "consent":
      return 0;
    case "document_capture":
      return 1;
    case "selfie_capture":
      return 2;
    case "liveness_check":
      return 3;
    case "processing":
    case "completed":
      return 4;
    default:
      return 0;
  }
}
