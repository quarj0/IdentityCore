"use client";

import { SubmitEvent, useEffect, useState } from "react";
import { ExternalLink, FileText, Loader2, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
} from "@identitycore/ui";
import { InlineStatus } from "@/components/feedback/inline-status";
import { getErrorMessage } from "@/lib/api-client";
import { getOnboardingRoute } from "@/lib/onboarding-state";
import {
  fetchCurrentOnboarding,
  createOrganizationDocumentUpload,
  deleteOrganizationDocument,
  submitOrganizationVerification,
  type OnboardingState,
} from "@/lib/onboarding-api";

const WORKSPACE_DASHBOARD_ORIGIN =
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export function OrganizationVerificationForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<{
    kind: "error" | "success";
    title: string;
    message: string;
  } | null>(null);
  const [form, setForm] = useState({
    businessRegistrationNumber: "",
    registeredAddress: "",
    officialWebsite: "",
    taxIdentificationNumber: "",
  });
  const [documents, setDocuments] = useState<
    Array<{ id: string; filename: string; storage_key: string; file_size_bytes: number; download_url?: string }>
  >([]);
  const [savedDocumentCount, setSavedDocumentCount] = useState(0);
  const [readOnly, setReadOnly] = useState(false);

  useEffect(() => {
    fetchCurrentOnboarding()
      .then((state) => {
        const nextRoute = getOnboardingRoute(state);
        setForm((current) => ({
          ...current,
          businessRegistrationNumber: state.businessRegistrationNumber || "",
          taxIdentificationNumber: state.taxIdentificationNumber || "",
          registeredAddress: state.registeredAddress || "",
          officialWebsite: state.officialWebsite || state.website || "",
        }));
        setDocuments(state.supportingDocuments || []);
        setSavedDocumentCount(state.supportingDocuments?.length || 0);
        setReadOnly(!state.organizationVerificationEditable);
        if (nextRoute !== "/onboarding/organization-verification") {
          router.replace(nextRoute);
        }
      })
      .catch((error) => {
        setFeedback({
          kind: "error",
          title: "Unable to load onboarding state",
          message: getErrorMessage(error),
        });
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFeedback(null);

    try {
      const result = await submitOrganizationVerification({
        ...form,
        supportingDocumentKeys: documents.map(
          (document) => document.storage_key,
        ),
      });
      setFeedback({
        kind: "success",
        title: "Organization details submitted",
        message:
          "Your onboarding record has been updated and the next step is ready.",
      });
      setReadOnly(true);
      setSavedDocumentCount(documents.length);
      const nextRoute =
        result.nextAction === "submit_administrator_identity_verification"
          ? "/onboarding/admin-identity"
          : getOnboardingRoute(result.onboarding);
      if (nextRoute === "/platform") {
        window.location.assign(WORKSPACE_DASHBOARD_ORIGIN.replace(/\/$/, ""));
        return;
      }
      router.replace(nextRoute);
    } catch (error) {
      setFeedback({
        kind: "error",
        title: "Unable to submit organization details",
        message: getErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
    }
  }

  function removeDocument(storageKey: string) {
    const document = documents.find((item) => item.storage_key === storageKey);
    if (!document) return;
    void (async () => {
      try {
        await deleteOrganizationDocument(document.id);
        setDocuments((current) =>
          current.filter((item) => item.storage_key !== storageKey),
        );
      } catch (error) {
        setFeedback({
          kind: "error",
          title: "Unable to delete document",
          message: getErrorMessage(error),
        });
      }
    })();
  }

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm md:col-span-2">
        <CardHeader>
          <CardTitle>Submit organization verification</CardTitle>
          <CardDescription className="leading-7">
            {readOnly
              ? "Submitted for review. Your organization details are read-only, but you can still add any missing supporting PDFs below."
              : "Provide your registration details and supporting PDF documents for review."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit}>
            {feedback ? (
              <div className="sm:col-span-2">
                <InlineStatus
                  kind={feedback.kind}
                  title={feedback.title}
                  message={feedback.message}
                />
              </div>
            ) : null}

            <div className="space-y-2">
              <Label htmlFor="businessRegistrationNumber">
                Business registration number
              </Label>
              <Input
                id="businessRegistrationNumber"
                value={form.businessRegistrationNumber}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    businessRegistrationNumber: event.target.value,
                  }))
                }
                required
                disabled={readOnly}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="taxIdentificationNumber">
                Tax identification number
              </Label>
              <Input
                id="taxIdentificationNumber"
                value={form.taxIdentificationNumber}
                disabled={readOnly}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    taxIdentificationNumber: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="officialWebsite">Official website</Label>
              <Input
                id="officialWebsite"
                type="url"
                disabled={readOnly}
                value={form.officialWebsite}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    officialWebsite: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="registeredAddress">Registered address</Label>
              <Textarea
                id="registeredAddress"
                value={form.registeredAddress}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    registeredAddress: event.target.value,
                  }))
                }
                required
                disabled={readOnly}
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="supportingDocuments">
                Supporting documents (PDF, 1&ndash;5 files, 10 MB each)
              </Label>
              {documents.length < 5 ? (
                <Input
                  id="supportingDocuments"
                  type="file"
                  accept="application/pdf,.pdf"
                  multiple
                  disabled={uploading || submitting}
                  onChange={async (event) => {
                    const files = Array.from(event.target.files || []);
                    if (documents.length + files.length > 5) {
                      setFeedback({
                        kind: "error",
                        title: "Too many documents",
                        message: "Upload no more than five PDF documents.",
                      });
                      return;
                    }
                    const invalid = files.find(
                      (file) => file.type.toLowerCase() !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf") || file.size <= 0 || file.size > 10 * 1024 * 1024,
                    );
                    if (invalid) {
                      setFeedback({ kind: "error", title: "Invalid document", message: "Choose non-empty PDF files no larger than 10 MB each." });
                      event.target.value = "";
                      return;
                    }
                    try {
                      setUploading(true);
                      const uploaded: OnboardingState["supportingDocuments"] = [];
                      for (const file of files) uploaded.push(await createOrganizationDocumentUpload(file));
                      setDocuments((current) => [...current, ...uploaded]);
                      event.target.value = "";
                    } catch (error) {
                      setFeedback({
                        kind: "error",
                        title: "Unable to upload document",
                        message: getErrorMessage(error),
                      });
                    } finally {
                      setUploading(false);
                    }
                  }}
                />
              ) : null}
              {documents.length === 0 ? <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-muted-foreground">No supporting documents have been uploaded yet. Choose at least one PDF above.</div> : null}
              <div className="grid gap-3 sm:grid-cols-2">
              {documents.map((document) => (
                <div
                  key={document.storage_key}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="flex min-w-0 items-center gap-3"><FileText className="h-5 w-5 shrink-0 text-red-600" /><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-900">{document.filename}</p><p className="text-xs text-muted-foreground">{Math.ceil(document.file_size_bytes / 1024)} KB · PDF</p></div></div>
                  <div className="flex items-center gap-2">
                    {document.download_url ? <Button asChild type="button" size="sm" variant="outline"><a href={document.download_url} target="_blank" rel="noreferrer"><ExternalLink className="h-4 w-4" />Preview</a></Button> : null}
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="text-slate-600 hover:text-red-600"
                      onClick={() => removeDocument(document.storage_key)}
                      disabled={uploading || submitting}
                      aria-label={`Remove ${document.filename}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              </div>
            </div>

            {(!readOnly || documents.length > savedDocumentCount) ? (
              <div className="sm:col-span-2">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full rounded-xl sm:w-auto"
                  disabled={submitting || uploading || documents.length === 0}
                >
                  {submitting || uploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : null}
                  {readOnly
                    ? "Submit supporting documents"
                    : "Save and continue"}
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
