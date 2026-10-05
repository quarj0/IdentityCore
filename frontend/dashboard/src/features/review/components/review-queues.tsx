"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  dashboardApi,
  ReviewQueue,
  ReviewQueueEntry,
} from "@/lib/dashboard-api";

export function ReviewQueues() {
  const [queues, setQueues] = useState<ReviewQueue[]>([]);
  const [selected, setSelected] = useState("");
  const [items, setItems] = useState<ReviewQueueEntry[]>([]);
  const [country, setCountry] = useState("");
  const [skill, setSkill] = useState("");
  const [overdue, setOverdue] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    if (!selected) return [];
    const filters = new URLSearchParams();
    if (country) filters.set("country", country);
    if (skill) filters.set("skill", skill);
    if (overdue) filters.set("overdue", "true");
    const page = await dashboardApi.queueCases(selected, filters);
    return page.results;
  }, [selected, country, skill, overdue]);
  useEffect(() => {
    let active = true;
    dashboardApi
      .reviewQueues()
      .then(({ queues: result }) => {
        if (active) setQueues(result);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    let active = true;
    load()
      .then((results) => {
        if (active) {
          setItems(results);
          setError("");
        }
      })
      .catch((caught) => {
        if (active) {
          setItems([]);
          setError(
            caught instanceof Error
              ? caught.message
              : "Queue could not be loaded.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [load]);
  async function assign() {
    if (busy || !selected) return;
    setBusy(true);
    setNotice("");
    setError("");
    try {
      const { assignment } = await dashboardApi.assignQueueCase(selected);
      setNotice(
        assignment
          ? `Assigned ${assignment.verification_id} to ${assignment.assigned_reviewer_id}.`
          : "No case currently has an eligible available reviewer.",
      );
      setItems(await load());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Assignment could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }
  if (!queues.length) return null;
  return (
    <section
      className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5"
      aria-label="Configured review queues"
    >
      <h2 className="font-semibold">Review queues</h2>
      <p className="text-sm text-slate-600">
        Assign the next case to the eligible reviewer with the smallest
        workload, then the longest time since their last assignment.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Queue
          <select
            aria-label="Review queue"
            disabled={busy}
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
            className="ml-2 rounded border p-2"
          >
            <option value="">Select a queue</option>
            {queues.map((queue) => (
              <option key={queue.queue_id} value={queue.queue_id}>
                {queue.name} · {queue.environment} · priority {queue.priority}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Country
          <input
            aria-label="Queue country"
            disabled={busy}
            maxLength={2}
            value={country}
            onChange={(event) => setCountry(event.target.value.toUpperCase())}
            className="ml-2 w-16 rounded border p-2"
          />
        </label>
        <label className="text-sm">
          Skill
          <input
            aria-label="Queue skill"
            disabled={busy}
            value={skill}
            onChange={(event) => setSkill(event.target.value)}
            className="ml-2 rounded border p-2"
          />
        </label>
        <label className="text-sm">
          <input
            type="checkbox"
            disabled={busy}
            checked={overdue}
            onChange={(event) => setOverdue(event.target.checked)}
          />{" "}
          Overdue only
        </label>
        <button
          type="button"
          disabled={!selected || busy}
          onClick={() => void assign()}
          className="rounded bg-blue-700 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {busy ? "Assigning…" : "Assign next case"}
        </button>
      </div>
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
      {selected && !items.length && !error && (
        <p className="text-sm text-slate-600">
          No queued cases match these filters.
        </p>
      )}
      {items.map((item) => (
        <Link
          key={item.verification_id}
          href={`/manual-review/${item.verification_id}`}
          className="block rounded border p-3 text-sm"
        >
          <span className="font-medium">{item.verification_id}</span> · priority{" "}
          {item.priority} · due {new Date(item.due_at).toLocaleString()}
          {item.overdue && (
            <strong className="ml-2 text-red-700">Overdue</strong>
          )}
          <p className="mt-1 text-slate-600">
            {item.country_code || "Country unknown"} ·{" "}
            {item.required_skills.join(", ") || "No required skills"} ·{" "}
            {item.assigned_reviewer_id || "Unassigned"}
          </p>
        </Link>
      ))}
    </section>
  );
}
