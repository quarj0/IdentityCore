"use client";

import { FormEvent, useEffect, useState } from "react";
import { Archive, GitBranch, Loader2, Rocket } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Policy } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveTemplateDetail({ id }: { id: string }) {
  const [item, setItem] = useState<Policy | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    dashboardApi.policy(id)
      .then(setItem)
      .catch((caught) => setError(messageOf(caught)));
  }, [id]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!item) return;
    const data = new FormData(event.currentTarget);
    setBusy("save");
    setMessage("");
    setError("");
    try {
      const result = await dashboardApi.patchPolicy(item.id, {
        name: String(data.get("name") || "").trim(),
        description: String(data.get("description") || "").trim(),
        required_document_types: String(data.get("required_document_types") || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        required_liveness_level: String(data.get("required_liveness_level") || "passive"),
        face_match_threshold: String(data.get("face_match_threshold") || "0.8500"),
        manual_review_threshold: String(data.get("manual_review_threshold") || "0.6500"),
        verification_expiry_minutes: Number(data.get("verification_expiry_minutes") || 1440),
        media_retention_days: Number(data.get("media_retention_days") || 30),
        metadata_retention_days: Number(data.get("metadata_retention_days") || 365),
      });
      setItem(result);
      setMessage("Draft template updated.");
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function act(action: "clone" | "activate" | "archive") {
    if (!item) return;
    setBusy(action);
    setMessage("");
    setError("");
    try {
      const result = await dashboardApi.policyAction(item.id, action);
      setMessage(
        action === "clone"
          ? `Created draft ${result.name} v${result.version}.`
          : `${result.name} v${result.version} is now ${result.status}.`,
      );
      if (action !== "clone") setItem(result);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  if (!item && !error) return <p className="text-sm text-slate-500">Loading template...</p>;
  if (!item) return <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">{error}</div>;

  const editable = item.status === "draft";

  return (
    <div className="space-y-8">
      <PageHeading
        title={`${item.name} v${item.version}`}
        description={editable ? "Draft templates can be edited before activation." : "Active and archived template versions are immutable. Clone to create a new draft."}
        action={<StatusBadge status={item.status} />}
      />

      {message ? <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">{message}</div> : null}
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => act("clone")} disabled={Boolean(busy)} className="rounded-xl">
          {busy === "clone" ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitBranch className="h-4 w-4" />}
          Clone new version
        </Button>
        {editable ? (
          <Button onClick={() => act("activate")} disabled={Boolean(busy)} className="rounded-xl">
            {busy === "activate" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
            Activate
          </Button>
        ) : null}
        {item.status !== "archived" ? (
          <Button variant="outline" onClick={() => act("archive")} disabled={Boolean(busy)} className="rounded-xl">
            {busy === "archive" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Archive className="h-4 w-4" />}
            Archive
          </Button>
        ) : null}
      </div>

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Policy settings</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={save} className="grid gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" defaultValue={item.name} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" defaultValue={item.description} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="required_document_types">Document types</Label>
              <Input id="required_document_types" name="required_document_types" defaultValue={item.required_document_types.join(", ")} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="required_liveness_level">Liveness</Label>
              <select
                id="required_liveness_level"
                name="required_liveness_level"
                defaultValue={item.required_liveness_level}
                disabled={!editable}
                className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm disabled:bg-slate-50"
              >
                <option value="passive">Passive</option>
                <option value="active">Active</option>
              </select>
            </div>
            <div>
              <Label htmlFor="face_match_threshold">Face threshold</Label>
              <Input id="face_match_threshold" name="face_match_threshold" defaultValue={item.face_match_threshold.toFixed(4)} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="manual_review_threshold">Review threshold</Label>
              <Input id="manual_review_threshold" name="manual_review_threshold" defaultValue={item.manual_review_threshold.toFixed(4)} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="verification_expiry_minutes">Expiry minutes</Label>
              <Input id="verification_expiry_minutes" name="verification_expiry_minutes" type="number" defaultValue={item.verification_expiry_minutes} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="media_retention_days">Media retention days</Label>
              <Input id="media_retention_days" name="media_retention_days" type="number" defaultValue={item.media_retention_days} disabled={!editable} />
            </div>
            <div>
              <Label htmlFor="metadata_retention_days">Metadata retention days</Label>
              <Input id="metadata_retention_days" name="metadata_retention_days" type="number" defaultValue={item.metadata_retention_days} disabled={!editable} />
            </div>
            {editable ? (
              <div className="md:col-span-3">
                <Button disabled={Boolean(busy)} className="rounded-xl">
                  {busy === "save" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  Save draft
                </Button>
              </div>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
