"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Button, Card, CardContent, Label } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi } from "@/lib/dashboard-api";

type Branding = {
  logo_url: string;
  logo_storage_key: string;
  primary_color: string;
  primary_text_color: string;
  background_color: string;
};

const DEFAULT_BRANDING: Branding = {
  logo_url: "",
  logo_storage_key: "",
  primary_color: "#2563eb",
  primary_text_color: "#ffffff",
  background_color: "#ffffff",
};

function toBranding(value: unknown): Branding {
  if (!value || typeof value !== "object") return DEFAULT_BRANDING;
  const source = value as Partial<Branding>;
  return {
    logo_url: typeof source.logo_url === "string" ? source.logo_url : "",
    logo_storage_key:
      typeof source.logo_storage_key === "string" ? source.logo_storage_key : "",
    primary_color: source.primary_color ?? DEFAULT_BRANDING.primary_color,
    primary_text_color:
      source.primary_text_color ?? DEFAULT_BRANDING.primary_text_color,
    background_color:
      source.background_color ?? DEFAULT_BRANDING.background_color,
  };
}

function luminance(color: string) {
  const channels = [1, 3, 5].map((index) => {
    const channel = Number.parseInt(color.slice(index, index + 2), 16) / 255;
    return channel <= 0.04045
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(first: string, second: string) {
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

export function LiveBrandingPage() {
  const [draft, setDraft] = useState<Branding>(DEFAULT_BRANDING);
  const [published, setPublished] = useState<Branding>(DEFAULT_BRANDING);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const environment =
    process.env.NEXT_PUBLIC_RUNTIME_ENVIRONMENT?.trim() || "current environment";

  useEffect(() => {
    dashboardApi.organization().then((organization) => {
      const settings = organization.settings;
      const savedDraft = toBranding(settings.branding_draft);
      const savedPublished = toBranding(
        settings.branding_published ?? {
          logo_url: settings.logo_url,
          logo_storage_key: settings.logo_storage_key,
          primary_color: settings.primary_color,
          primary_text_color: settings.primary_text_color,
          background_color: settings.background_color,
        },
      );
      setDraft(savedDraft);
      setPublished(savedPublished);
    }).catch(() => setError("Unable to load organization branding."));
  }, []);

  const primaryContrast = contrastRatio(
    draft.primary_color,
    draft.primary_text_color,
  );
  const backgroundContrast = contrastRatio(
    "#111827",
    draft.background_color,
  );
  const canPublish = primaryContrast >= 4.5 && backgroundContrast >= 4.5;

  async function uploadLogo() {
    if (!file) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const target = await dashboardApi.createBrandingUpload({
        asset_type: "logo",
        filename: file.name,
        mime_type: file.type,
        file_size_bytes: file.size,
      });
      const response = await fetch(target.upload_url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": file.type,
          "x-amz-server-side-encryption": "AES256",
        },
      });
      if (!response.ok) throw new Error("The logo upload failed.");
      setDraft((current) => ({
        ...current,
        logo_storage_key: target.storage_key,
        logo_url: target.asset_url,
      }));
      setFile(null);
      setMessage("Logo uploaded to the draft preview. Save the draft or publish it to this environment.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to upload logo.");
    } finally {
      setBusy(false);
    }
  }

  async function saveBranding(publish: boolean) {
    if (publish && !canPublish) {
      setError("Improve the color contrast before publishing.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const organization = await dashboardApi.updateBranding({
        ...(draft.logo_storage_key
          ? { logo_storage_key: draft.logo_storage_key }
          : {}),
        primary_color: draft.primary_color,
        primary_text_color: draft.primary_text_color,
        background_color: draft.background_color,
        publish,
      });
      const saved = toBranding(
        publish
          ? organization.settings.branding_published
          : organization.settings.branding_draft,
      );
      setDraft(saved);
      if (publish) {
        setPublished(saved);
        setMessage("Branding published to " + environment + ".");
      } else {
        setMessage("Draft saved for " + environment + " preview.");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save branding.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <PageHeading
        title="Branding"
        description="Preview organization branding, check accessible colors, and publish it to the current environment."
      />
      <Card>
        <CardContent className="grid gap-8 p-6 lg:grid-cols-2">
          <section className="space-y-5" aria-labelledby="branding-settings-title">
            <h2 id="branding-settings-title" className="text-lg font-semibold">
              Draft settings
            </h2>
            <p className="text-sm text-muted-foreground">
              Current environment: <strong>{environment}</strong>
            </p>
            <div>
              <Label htmlFor="branding-logo">Organization logo</Label>
              <input
                id="branding-logo"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="mt-2 block text-sm"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                PNG, JPEG, or WebP up to 5 MB. SVG files are not accepted.
              </p>
              <Button className="mt-3" onClick={uploadLogo} disabled={!file || busy}>
                {busy ? "Uploading..." : "Upload draft logo"}
              </Button>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <ColorField
                id="primary-color"
                label="Button color"
                value={draft.primary_color}
                onChange={(value) =>
                  setDraft((current) => ({ ...current, primary_color: value }))
                }
              />
              <ColorField
                id="primary-text-color"
                label="Button text"
                value={draft.primary_text_color}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    primary_text_color: value,
                  }))
                }
              />
              <ColorField
                id="background-color"
                label="Preview background"
                value={draft.background_color}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    background_color: value,
                  }))
                }
              />
            </div>
            <div className="space-y-1 text-sm">
              <p className={primaryContrast < 4.5 ? "text-destructive" : "text-muted-foreground"}>
                Button contrast: {primaryContrast.toFixed(2)}:1 (minimum 4.5:1)
              </p>
              <p className={backgroundContrast < 4.5 ? "text-destructive" : "text-muted-foreground"}>
                Preview text contrast: {backgroundContrast.toFixed(2)}:1 (minimum 4.5:1)
              </p>
              {!canPublish ? (
                <p role="alert" className="text-sm text-destructive">
                  Publishing is blocked until both text combinations meet WCAG AA contrast.
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                onClick={() => void saveBranding(false)}
                disabled={busy}
              >
                Save draft
              </Button>
              <Button
                onClick={() => void saveBranding(true)}
                disabled={busy || !canPublish}
              >
                Publish to {environment}
              </Button>
            </div>
          </section>

          <section aria-labelledby="branding-preview-title">
            <h2 id="branding-preview-title" className="mb-3 text-lg font-semibold">
              Applicant preview
            </h2>
            <div
              className="min-h-72 rounded-2xl border p-6"
              style={{ backgroundColor: draft.background_color, color: "#111827" }}
            >
              <div className="flex items-center gap-3 border-b border-black/10 pb-4">
                {draft.logo_url ? (
                  <Image
                    src={draft.logo_url}
                    alt="Organization logo preview"
                    width={160}
                    height={64}
                    unoptimized
                    className="h-16 max-w-40 object-contain"
                  />
                ) : (
                  <span className="text-sm font-semibold">Organization logo preview</span>
                )}
              </div>
              <h3 className="mt-6 text-xl font-semibold">Verify your identity</h3>
              <p className="mt-2 text-sm">
                Review the organization name and consent before continuing.
              </p>
              <button
                type="button"
                className="mt-6 rounded-lg px-4 py-2 text-sm font-semibold"
                style={{
                  backgroundColor: draft.primary_color,
                  color: draft.primary_text_color,
                }}
              >
                Continue
              </button>
              <p className="mt-5 text-xs text-muted-foreground">
                Published version: {published.primary_color}
              </p>
            </div>
          </section>
        </CardContent>
      </Card>
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}
      {message ? <p role="status" className="text-sm">{message}</p> : null}
    </div>
  );
}

function ColorField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <input
        id={id}
        type="color"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full cursor-pointer rounded border border-border bg-background p-1"
      />
      <output htmlFor={id} className="text-xs text-muted-foreground">
        {value}
      </output>
    </div>
  );
}
