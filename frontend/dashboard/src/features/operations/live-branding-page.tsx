"use client";

import { useEffect, useState } from "react";
import { Button, Card, CardContent, Label } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi } from "@/lib/dashboard-api";

export function LiveBrandingPage() {
  const [logoUrl, setLogoUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => { dashboardApi.organization().then((organization) => setLogoUrl(String(organization.settings.logo_url ?? ""))); }, []);

  async function upload() {
    if (!file) return;
    setBusy(true);
    try {
      const target = await dashboardApi.createBrandingUpload({ asset_type: "logo", filename: file.name, mime_type: file.type });
      const response = await fetch(target.upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type, "x-amz-server-side-encryption": "AES256" } });
      if (!response.ok) throw new Error("The logo upload failed.");
      const organization = await dashboardApi.updateBranding({ logo_storage_key: target.storage_key });
      setLogoUrl(String(organization.settings.logo_url ?? target.asset_url)); setMessage("Branding logo saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to upload logo."); }
    finally { setBusy(false); }
  }

  return <div className="space-y-8"><PageHeading title="Branding" description="Customize the logo shown in hosted verification experiences."/><Card><CardContent className="space-y-6 p-6">{logoUrl ? <img src={logoUrl} alt="Current organization logo" className="h-20 max-w-64 object-contain" /> : <div className="flex h-20 w-64 items-center justify-center rounded-xl border border-dashed text-sm text-slate-500">No logo uploaded</div>}<div><Label htmlFor="branding-logo">Organization logo</Label><input id="branding-logo" type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" className="mt-2 block text-sm" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></div><Button onClick={upload} disabled={!file || busy}>{busy ? "Uploading..." : "Upload logo"}</Button>{message ? <p role="status" className="text-sm">{message}</p> : null}</CardContent></Card></div>;
}
