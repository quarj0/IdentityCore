"use client";

import { useCallback, useEffect, useState } from "react";
import { restRequest } from "@/lib/api-client";

type Capability = { countries: string[]; document_types: string[]; input_schema: string; output_schema: string };
type Provider = { id: string; name: string; tenant_id: string | null; manifest: { capabilities?: Record<string, Capability> } };
type Configuration = { id: string; environment: string; version: number; status: string; configuration: { endpoint_url: string }; diff: Record<string, { before: unknown; after: unknown }>; tested_at: string | null; test_succeeded: boolean; approved_by: string | null };
const capabilitiesByType: Record<string, string[]> = {
  document: ["document_quality", "document_classification", "document_ocr"],
  biometric: ["face_match", "liveness"], liveness: ["liveness"],
  risk: ["risk_check"], identity_database: ["identity_lookup"],
};
const split = (value: string) => value.split(",").map((part) => part.trim()).filter(Boolean);
const inputClass = "w-full rounded-lg border border-slate-300 p-2";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerId, setProviderId] = useState("");
  const [configs, setConfigs] = useState<Configuration[]>([]);
  const [configId, setConfigId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [providerType, setProviderType] = useState("document");
  const [secret, setSecret] = useState("");
  const selected = configs.find((item) => item.id === configId);
  const provider = providers.find((item) => item.id === providerId);
  const reload = useCallback(async (id: string) => {
    const result = await restRequest<{ results: Configuration[] }>(`/providers/${id}/configurations/`);
    setConfigs(result.results);
  }, []);
  useEffect(() => {
    let live = true;
    restRequest<{ results: Provider[] }>("/providers/").then((result) => { if (live) setProviders(result.results.filter((item) => item.tenant_id)); }).catch(() => { if (live) setMessage("Provider setup could not be loaded."); });
    return () => { live = false; };
  }, []);
  useEffect(() => {
    let live = true;
    if (providerId) restRequest<{ results: Configuration[] }>(`/providers/${providerId}/configurations/`).then((result) => { if (live) setConfigs(result.results); }).catch(() => { if (live) setMessage("Provider management permission is required."); });
    return () => { live = false; };
  }, [providerId]);
  async function perform(action: () => Promise<void>) {
    setBusy(true); setMessage("");
    try { await action(); } catch (error) { setMessage(error instanceof Error ? error.message : "The provider action failed."); }
    finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-5xl space-y-6 p-6">
    <h1 className="text-2xl font-semibold">Providers</h1>
    <p>Declare provider coverage, test sandbox credentials, and request an independently approved production configuration.</p>
    <p role="status" aria-live="polite">{message}</p>
    <section className="rounded-xl border p-5">
      <h2 className="mb-3 text-xl font-semibold">Add a provider</h2>
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => {
        event.preventDefault(); const data = new FormData(event.currentTarget);
        void perform(async () => {
          const countries = split(String(data.get("countries"))).map((value) => value.toUpperCase());
          const documentTypes = split(String(data.get("documents")));
          const capabilities = Object.fromEntries(data.getAll("capabilities").map((key) => [String(key), { countries, document_types: documentTypes, input_schema: `${key}.input/v1`, output_schema: `${key}.output/v1` }]));
          const result = await restRequest<Provider>("/providers/setup/", { method: "POST", body: JSON.stringify({ name: data.get("name"), provider_type: providerType, manifest: { manifest_version: "1", contract_version: "1", capabilities, environments: ["sandbox", "production"], residency: split(String(data.get("regions"))), retention_days: Number(data.get("retention")), processor: data.get("processor"), transfer_notes: data.get("transfers") } }) });
          setProviders((items) => [...items, result]); setConfigs([]); setConfigId(""); setProviderId(result.id); setMessage("Provider added. Configure and test its sandbox connection.");
        });
      }}>
        <label>Name<input className={inputClass} name="name" required maxLength={255} /></label>
        <label>Provider type<select className={inputClass} value={providerType} onChange={(event) => setProviderType(event.target.value)}>{Object.keys(capabilitiesByType).map((type) => <option key={type}>{type}</option>)}</select></label>
        <fieldset className="sm:col-span-2"><legend>Capabilities</legend>{capabilitiesByType[providerType].map((key) => <label key={key} className="mr-4 inline-flex gap-2"><input type="checkbox" name="capabilities" value={key} />{key.replaceAll("_", " ")}</label>)}</fieldset>
        <label>Countries (comma separated; * for all)<input className={inputClass} name="countries" defaultValue="*" required /></label>
        <label>Document types (comma separated; * for all)<input className={inputClass} name="documents" defaultValue="*" required /></label>
        <label>Processing regions<input className={inputClass} name="regions" placeholder="eu-west-1" required /></label>
        <label>Provider retention in days<input className={inputClass} name="retention" type="number" min={0} max={36500} required /></label>
        <label>Processor name<input className={inputClass} name="processor" maxLength={1000} required /></label>
        <label>Transfer safeguards<textarea className={inputClass} name="transfers" maxLength={1000} required /></label>
        <button className="rounded-lg bg-blue-700 p-2 text-white disabled:opacity-50" disabled={busy}>Add provider</button>
      </form>
    </section>
    <section className="space-y-4 rounded-xl border p-5">
      <h2 className="text-xl font-semibold">Connections and promotion</h2>
      <label>Provider<select className={inputClass} disabled={busy} value={providerId} onChange={(event) => { setConfigs([]); setConfigId(""); setProviderId(event.target.value); }}><option value="">Choose provider</option>{providers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {providerId && <>
        <label>Configuration<select className={inputClass} disabled={busy} value={configId} onChange={(event) => setConfigId(event.target.value)}><option value="">Choose configuration</option>{configs.map((item) => <option key={item.id} value={item.id}>{item.environment} v{item.version} — {item.status}</option>)}</select></label>
        {selected && <div className="space-y-2">
          <p>{selected.configuration.endpoint_url}</p>
          <p>Connection test: {selected.test_succeeded ? "passed" : "not passed"}{selected.tested_at ? ` at ${selected.tested_at}` : ""}. Activation requires a pass within 15 minutes.</p>
          <h3 className="font-semibold">Configuration changes</h3>
          <ul>{Object.entries(selected.diff).map(([key, change]) => <li key={key}>{key.replaceAll("_", " ")}: {JSON.stringify(change.before)} → {JSON.stringify(change.after)}</li>)}</ul>
          {selected.status === "draft" && <div className="flex gap-3">{["test", "activate"].map((action) => <button key={action} disabled={busy} className="rounded-lg border p-2" onClick={() => void perform(async () => {
            const result = await restRequest<Configuration>(`/providers/configurations/${selected.id}/${action}/`, { method: "POST", body: "{}" }); await reload(providerId); setMessage(action === "test" ? (result.test_succeeded ? "Connection test passed." : "Connection test failed; check the provider contract and credentials.") : "Configuration activated.");
          })}>{action === "test" ? "Test connection" : selected.environment === "production" ? "Approve production" : "Activate sandbox"}</button>)}</div>}
          {selected.status === "active" && <form className="flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); const key = String(data.get("capability")); const coverage = provider?.manifest.capabilities?.[key]; void perform(async () => {
            await restRequest(`/providers/configurations/${selected.id}/assign/`, { method: "POST", body: JSON.stringify({ capability: key, countries: coverage?.countries.filter((value) => value !== "*"), document_types: coverage?.document_types.filter((value) => value !== "*") }) }); setMessage("Environment-scoped route published.");
          }); }}><label>Assign capability<select className={inputClass} name="capability">{Object.keys(provider?.manifest.capabilities || {}).map((key) => <option key={key}>{key}</option>)}</select></label><button disabled={busy} className="rounded-lg border p-2">Publish assignment</button></form>}
        </div>}
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => {
          event.preventDefault(); const data = new FormData(event.currentTarget); const environment = String(data.get("environment"));
          void perform(async () => {
            const endpoint = String(data.get("endpoint")); const result = await restRequest<Configuration>(`/providers/${providerId}/configurations/`, { method: "POST", body: JSON.stringify({ environment, configuration: { endpoint_url: endpoint, allowed_hosts: [new URL(endpoint).hostname], timeout_seconds: 15 }, credentials: { api_key: secret }, ...(environment === "production" ? { source_id: selected?.id } : {}) }) });
            setSecret(""); await reload(providerId); setConfigId(result.id); setMessage("Configuration requested. Test this exact version before activation.");
          });
        }}>
          <label>Environment<select className={inputClass} name="environment"><option value="sandbox">Sandbox</option><option value="production">Production promotion</option></select></label>
          <label>HTTPS endpoint<input className={inputClass} name="endpoint" type="url" required /></label>
          <label>New environment credential<input className={inputClass} type="password" autoComplete="new-password" minLength={16} required value={secret} onChange={(event) => setSecret(event.target.value)} /></label>
          <p>For production, select an active sandbox source above. Supply a separate production credential. A different user with promotion approval permission must approve.</p>
          <button disabled={busy} className="rounded-lg bg-blue-700 p-2 text-white disabled:opacity-50">Request configuration</button>
        </form>
      </>}
    </section>
  </div>;
}
