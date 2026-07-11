"use client";

import { SubmitEvent, useEffect, useState } from "react";
import { Check, Copy, KeyRound, Loader2 } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { APIClient, dashboardApi, Project } from "@/lib/dashboard-api";

const defaultScopes = ["verifications:read", "verifications:create"];

function messageOf(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

export function LiveApiKeysPage() {
  const [items, setItems] = useState<APIClient[]>([]);
  const [secret, setSecret] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [pendingApproval, setPendingApproval] = useState(false);
  const [copied, setCopied] = useState(false);
  const [acting, setActing] = useState("");
  const hasUsableKey = items.some((item) => item.status !== "revoked");

  async function load() {
    setError("");
    try {
      const response = await dashboardApi.apiClients();
      setItems(response.results);
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    dashboardApi
      .apiClients()
      .then((response) => setItems(response.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { dashboardApi.organization().then((organization) => setPendingApproval(organization.status !== "active")).catch(() => undefined); }, []);
  useEffect(() => {
    dashboardApi
      .projects()
      .then((response) => setProjects(response.results))
      .catch(() => undefined);
  }, []);

  async function create(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setCreating(true);
    setSecret("");
    setMessage("");
    setError("");
    try {
      const result = await dashboardApi.createApiClient({
        project_id: String(data.get("project_id") || ""),
        name: String(data.get("name") || "").trim(),
        scopes: data.getAll("scopes").map(String),
        allowed_networks: String(data.get("allowed_networks") || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        rate_limit_per_minute: Number(data.get("rate_limit_per_minute") || 60),
      });
      setSecret(`${result.client_id}:${result.client_secret ?? ""}`);
      setMessage(
        "API key created. Save the client secret now; it will not be shown again.",
      );
      form.reset();
      await load();
    } catch (caught) {
      setError(messageOf(caught));
    } finally {
      setCreating(false);
    }
  }

  async function keyAction(item: APIClient, action: "rotate" | "revoke") {
    const warning = action === "rotate" ? "Rotate this key? The current secret will stop working immediately." : "Revoke this key? Applications using it will immediately lose access.";
    if (!window.confirm(warning)) return;
    setActing(item.public_id); setError(""); setMessage("");
    try {
      const result = await dashboardApi.apiClientAction(item.public_id, action);
      if (action === "rotate") {
        setSecret(`${result.client_id}:${result.client_secret ?? ""}`);
        setMessage("API key rotated. Copy the new secret now; it will not be shown again.");
      } else {
        setSecret(""); setMessage("API key revoked. You can create a replacement sandbox key.");
      }
      await load();
    } catch (caught) { setError(messageOf(caught)); } finally { setActing(""); }
  }

  return (
    <div className="space-y-8">
      <PageHeading
        title="API keys"
        description="Manage sandbox and production credentials for your workspace."
      />
      {message ? (
        <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}
      {secret ? (
        <div className="flex gap-2"><Input readOnly value={secret} aria-label="New API client credentials" className="font-mono" /><Button type="button" variant="outline" onClick={async () => { await navigator.clipboard.writeText(secret); setCopied(true); window.setTimeout(() => setCopied(false), 2000); }}>{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}{copied ? "Copied" : "Copy"}</Button></div>
      ) : null}

      {pendingApproval && hasUsableKey ? <Card className="rounded-2xl border-amber-200 bg-amber-50"><CardContent className="p-5 text-sm text-amber-900"><p className="font-semibold">Sandbox test-key limit reached</p><p className="mt-1">Pending workspaces can keep one test key with verification read/create scopes and a 30 requests-per-minute limit. Rotate it if the secret was missed, or revoke it to create a replacement.</p></CardContent></Card> : <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Create API key</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="project_id">Project</Label>
              <select
                id="project_id"
                name="project_id"
                required
                className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
              >
                <option value="">Choose a project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} ({project.environment})
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-500">
                Sandbox keys are available now. Production keys require platform
                approval.
              </p>
            </div>
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                name="name"
                required
                placeholder="Production backend"
              />
            </div>
            <div>
              <Label htmlFor="rate_limit_per_minute">
                Rate limit per minute
              </Label>
              <Input
                id="rate_limit_per_minute"
                name="rate_limit_per_minute"
                type="number"
                defaultValue={pendingApproval ? "30" : "60"}
                max={pendingApproval ? 30 : undefined}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="allowed_networks">Allowed networks</Label>
              <Input
                id="allowed_networks"
                name="allowed_networks"
                placeholder="Optional comma-separated CIDRs"
              />
            </div>
            <div className="md:col-span-2">
              <Label>Scopes</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {defaultScopes.map((scope) => (
                  <label
                    key={scope}
                    className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  >
                    <input
                      name="scopes"
                      value={scope}
                      type="checkbox"
                      defaultChecked
                    />
                    {scope}
                  </label>
                ))}
              </div>
            </div>
            <div className="md:col-span-2">
              <Button disabled={creating} className="rounded-xl">
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Create API key
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>}

      {loading ? (
        <p className="text-sm text-slate-500">Loading API keys...</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={KeyRound}
          title="No API keys yet"
          description="Create an API key to start testing IdentityCore."
        />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <Card
              key={item.public_id}
              className="rounded-2xl border-slate-200 shadow-sm"
            >
              <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
                <div>
                  <p className="font-medium text-slate-950">{item.name}</p>
                  <p className="mt-1 font-mono text-sm text-slate-500">
                    {item.client_id}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <span className="text-sm text-slate-500">
                    {item.scopes.join(", ")}
                  </span>
                  {item.status !== "revoked" ? <><Button size="sm" variant="outline" disabled={acting === item.public_id} onClick={() => keyAction(item, "rotate")}>Rotate secret</Button><Button size="sm" variant="destructive" disabled={acting === item.public_id} onClick={() => keyAction(item, "revoke")}>Revoke</Button></> : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
