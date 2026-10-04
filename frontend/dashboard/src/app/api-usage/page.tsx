"use client";
import { useCallback, useEffect, useState } from "react";
import { restRequest } from "@/lib/api-client";

type WindowUsage = { limit: number; accepted: number; denied: number; remaining: number; resets_at: string };
type Usage = { environment: string; minute: WindowUsage; month: WindowUsage };
export default function APIUsagePage() {
  const [usage, setUsage] = useState<Usage[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    try { setUsage((await restRequest<{ results: Usage[] }>("/api-clients/usage")).results); }
    catch { setError("API usage could not be loaded. Organization access is required."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    let active = true;
    void restRequest<{ results: Usage[] }>("/api-clients/usage")
      .then((response) => { if (active) setUsage(response.results); })
      .catch(() => { if (active) setError("API usage could not be loaded. Organization access is required."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  return <div className="space-y-6 p-6">
    <h1 className="text-2xl font-semibold">API usage</h1>
    <p>Organization quotas are shared by API clients within each environment. Counts include requests admitted by the quota check, even when a later operation fails.</p>
    <button className="rounded-lg border p-2" disabled={loading} onClick={() => { setLoading(true); setError(""); void load(); }}>{loading ? "Loading..." : "Refresh usage"}</button>
    {error && <p role="alert">{error}</p>}
    {usage.map((item) => <section key={item.environment} className="rounded-xl border p-4">
      <h2 className="text-xl font-semibold capitalize">{item.environment}</h2>
      <div className="overflow-x-auto"><table className="w-full text-left"><thead><tr>{["Window", "Limit", "Admitted", "Denied", "Remaining", "Resets"].map((name) => <th className="p-2" key={name}>{name}</th>)}</tr></thead>
        <tbody>{(["minute", "month"] as const).map((period) => <tr key={period}><td className="p-2">{period}</td><td className="p-2">{item[period].limit.toLocaleString()}</td><td className="p-2">{item[period].accepted.toLocaleString()}</td><td className="p-2">{item[period].denied.toLocaleString()}</td><td className="p-2">{item[period].remaining.toLocaleString()}</td><td className="p-2">{new Date(item[period].resets_at).toLocaleString()}</td></tr>)}</tbody>
      </table></div>
    </section>)}
  </div>;
}
