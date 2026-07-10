"use client";

import { FormEvent, useEffect, useState } from "react";
import { Loader2, Send, Webhook } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, supportedWebhookEvents, WebhookEndpoint } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveWebhooksPage() {
  const [items, setItems] = useState<WebhookEndpoint[]>([]);
  const [secret, setSecret] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    setError("");
    try {
      const response = await dashboardApi.webhooks();
      setItems(response.results);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    dashboardApi.webhooks()
      .then((response) => setItems(response.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy("create");
    setSecret("");
    setMessage("");
    setError("");
    try {
      const result = await dashboardApi.createWebhook({
        url: String(data.get("url") || "").trim(),
        description: String(data.get("description") || "").trim(),
        events: data.getAll("events").map(String),
      });
      setSecret(result.secret);
      setMessage("Webhook endpoint created. Save the signing secret now; it will not be shown again.");
      form.reset();
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  async function testEndpoint(id: string) {
    setBusy(id);
    setMessage("");
    setError("");
    try {
      await dashboardApi.testWebhook(id);
      setMessage("Webhook test event queued.");
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="space-y-8">
      <PageHeading title="Webhooks" description="Send verification lifecycle events to your application." />
      {message ? <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">{message}</div> : null}
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {secret ? <Input readOnly value={secret} aria-label="New webhook signing secret" className="font-mono" /> : null}

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader><CardTitle>Add endpoint</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="url">Endpoint URL</Label>
              <Input id="url" name="url" type="url" required placeholder="https://example.com/webhooks/identitycore" />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" placeholder="Production events" />
            </div>
            <div className="md:col-span-2">
              <Label>Events</Label>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                {supportedWebhookEvents.map((event) => (
                  <label key={event} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
                    <input name="events" value={event} type="checkbox" defaultChecked={event === "verification.created" || event === "verification.verified" || event === "verification.rejected"} />
                    {event}
                  </label>
                ))}
              </div>
            </div>
            <div className="md:col-span-2">
              <Button disabled={Boolean(busy)} className="rounded-xl">
                {busy === "create" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Add webhook
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-sm text-slate-500">Loading webhooks...</p>
      ) : items.length === 0 ? (
        <EmptyState icon={Webhook} title="No webhook endpoints" description="Add an endpoint to receive verification events." />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <Card key={item.id} className="rounded-2xl border-slate-200 shadow-sm">
              <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
                <div>
                  <p className="font-medium text-slate-950">{item.url}</p>
                  <p className="mt-1 text-sm text-slate-500">{item.events.join(", ")}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={item.status} />
                  <Button variant="outline" className="rounded-xl" onClick={() => testEndpoint(item.id)} disabled={Boolean(busy)}>
                    {busy === item.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
