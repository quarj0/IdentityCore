"use client";

import { useCallback, useEffect, useState } from "react";
import { dashboardApi, QualitySample } from "@/lib/dashboard-api";

export function ReviewQuality() {
  const [environment, setEnvironment] = useState("sandbox");
  const [samples, setSamples] = useState<QualitySample[]>([]);
  const [report, setReport] = useState<{
    completed: number;
    agreements: number;
    disagreements: number;
    pending: number;
  } | null>(null);
  const [selected, setSelected] = useState("");
  const [outcome, setOutcome] = useState("verified");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const load = useCallback(
    () => dashboardApi.qualitySamples(environment),
    [environment],
  );
  useEffect(() => {
    let active = true;
    load()
      .then((page) => {
        if (active) setSamples(page.results);
      })
      .catch(() => {
        if (active) setSamples([]);
      });
    dashboardApi
      .qualityReport(environment)
      .then((result) => {
        if (active) setReport(result);
      })
      .catch(() => {
        if (active) setReport(null);
      });
    return () => {
      active = false;
    };
  }, [load, environment]);
  const sample = samples.find((item) => item.id === selected);
  const codes = sample?.reason_rules.outcomes?.[outcome]?.codes ?? [
    `quality_${outcome}`,
  ];
  async function act(item: QualitySample, allocate: boolean) {
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      if (allocate) await dashboardApi.allocateQuality(item.id, environment);
      else
        await dashboardApi.decideQuality(
          item.id,
          environment,
          outcome,
          reason || codes[0],
          notes,
        );
      const page = await load();
      setSamples(page.results);
      setSelected("");
      setNotes("");
      setReason("");
      setNotice(
        allocate
          ? "Quality assignment updated."
          : "Quality outcome recorded. The applicant's result is unchanged.",
      );
      try {
        setReport(await dashboardApi.qualityReport(environment));
      } catch {
        setReport(null);
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quality review could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      aria-label="Review quality"
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-semibold">Review quality</h2>
        <label className="text-sm">
          Environment
          <select
            aria-label="Quality environment"
            disabled={busy}
            value={environment}
            onChange={(event) => {
              setEnvironment(event.target.value);
              setSamples([]);
              setReport(null);
              setSelected("");
              setNotes("");
              setReason("");
            }}
            className="ml-2 rounded border p-2"
          >
            <option value="sandbox">Sandbox</option>
            <option value="production">Production</option>
          </select>
        </label>
      </div>
      <p className="text-sm text-slate-600">
        Independent quality assessments record agreement or disagreement without
        changing the final verification result.
      </p>
      {report && (
        <p className="text-sm">
          {report.completed} completed · {report.agreements} agreements ·{" "}
          {report.disagreements} disagreements · {report.pending} pending
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="text-sm text-slate-700">
          {notice}
        </p>
      )}
      {!samples.length && (
        <p className="text-sm text-slate-600">
          No quality assignments are available to you.
        </p>
      )}
      {samples.map((item) => (
        <div key={item.id} className="space-y-2 rounded border p-3 text-sm">
          <p className="font-medium">
            {item.verification_id} · original outcome: {item.original_outcome}
          </p>
          <p>Reasons: {item.original_reason_codes.join(", ") || "None"}</p>
          {item.can_review && (
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setSelected(item.id);
                setOutcome("verified");
                setReason("");
                setNotes("");
              }}
              className="rounded border px-3 py-2"
            >
              Assess quality
            </button>
          )}
          {!item.reviewer_id && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void act(item, true)}
              className="rounded border px-3 py-2"
            >
              Allocate independent reviewer
            </button>
          )}
        </div>
      ))}
      {sample && (
        <form
          className="space-y-3 rounded border p-4"
          onSubmit={(event) => {
            event.preventDefault();
            void act(sample, false);
          }}
        >
          <p className="font-medium">Assess {sample.verification_id}</p>
          <label className="block text-sm">
            Quality outcome
            <select
              aria-label="Quality outcome"
              disabled={busy}
              value={outcome}
              onChange={(event) => {
                setOutcome(event.target.value);
                setReason("");
              }}
              className="ml-2 rounded border p-2"
            >
              <option value="verified">Verified</option>
              <option value="rejected">Rejected</option>
              <option value="failed">Failed</option>
            </select>
          </label>
          <label className="block text-sm">
            Quality reason
            <select
              aria-label="Quality reason"
              disabled={busy}
              value={reason || codes[0]}
              onChange={(event) => setReason(event.target.value)}
              className="ml-2 rounded border p-2"
            >
              {codes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Quality notes
            <textarea
              aria-label="Quality notes"
              disabled={busy}
              required={
                sample.reason_rules.outcomes?.[outcome]?.notes_required ?? false
              }
              maxLength={4000}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="mt-1 block w-full rounded border p-2"
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="rounded bg-blue-700 px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {busy ? "Saving…" : "Record quality outcome"}
          </button>
        </form>
      )}
    </section>
  );
}
