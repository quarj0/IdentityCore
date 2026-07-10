"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { FileText, Loader2, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Policy } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveTemplatesPage() {
  const [items, setItems] = useState<Policy[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function load() {
    setError("");
    try {
      setItems(await dashboardApi.policies());
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    dashboardApi.policies()
      .then(setItems)
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setCreating(true);
    setError("");
    try {
      await dashboardApi.createPolicy({
        name: String(data.get("name") || "").trim(),
        description: String(data.get("description") || "").trim(),
        required_document_types: String(data.get("required_document_types") || "national_id")
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
      form.reset();
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-8">
      <PageHeading
        title="Verification templates"
        description="Manage versioned verification policies used by hosted verification requests."
        action={
          <Button variant="outline" className="rounded-xl" onClick={() => void load()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />

      {error ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>New draft template</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" required placeholder="Standard KYC" />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" placeholder="Document, selfie, liveness" />
            </div>
            <div>
              <Label htmlFor="required_document_types">Document types</Label>
              <Input id="required_document_types" name="required_document_types" defaultValue="national_id" />
            </div>
            <div>
              <Label htmlFor="required_liveness_level">Liveness</Label>
              <select id="required_liveness_level" name="required_liveness_level" className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm">
                <option value="passive">Passive</option>
                <option value="active">Active</option>
              </select>
            </div>
            <div>
              <Label htmlFor="face_match_threshold">Face threshold</Label>
              <Input id="face_match_threshold" name="face_match_threshold" defaultValue="0.8500" />
            </div>
            <div>
              <Label htmlFor="manual_review_threshold">Review threshold</Label>
              <Input id="manual_review_threshold" name="manual_review_threshold" defaultValue="0.6500" />
            </div>
            <div>
              <Label htmlFor="verification_expiry_minutes">Expiry minutes</Label>
              <Input id="verification_expiry_minutes" name="verification_expiry_minutes" type="number" defaultValue="1440" />
            </div>
            <div>
              <Label htmlFor="media_retention_days">Media retention days</Label>
              <Input id="media_retention_days" name="media_retention_days" type="number" defaultValue="30" />
            </div>
            <div>
              <Label htmlFor="metadata_retention_days">Metadata retention days</Label>
              <Input id="metadata_retention_days" name="metadata_retention_days" type="number" defaultValue="365" />
            </div>
            <div className="md:col-span-3">
              <Button disabled={creating} className="rounded-xl">
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Create draft
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-sm text-slate-500">Loading templates...</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No templates"
          description="Create a draft template, activate it, then use it for dashboard verification requests."
        />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <Link key={item.id} href={`/templates/${item.id}`} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-blue-200 hover:bg-blue-50/30">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-950">{item.name} v{item.version}</p>
                  <p className="mt-1 text-sm text-slate-500">{item.description || "No description"}</p>
                </div>
                <StatusBadge status={item.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
