"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, ManualReviewSummary } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveReviewList() {
  const [items, setItems] = useState<ManualReviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi.manualReviews()
      .then((page) => setItems(page.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading
        title="Manual review"
        description="Review evidence summaries and record auditable verification decisions."
      />

      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      {loading ? (
        <p className="text-sm text-slate-500">Loading manual-review queue...</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No cases require review"
          description="Verifications that need manual attention will appear here."
        />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <Link
              key={item.verification_id}
              href={`/manual-review/${item.verification_id}`}
              className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-blue-200 hover:bg-blue-50/30"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-950">
                    {item.subject?.full_name || item.subject?.email || item.verification_id}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {item.purpose} · {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.risk_level || "risk pending"} />
                  <StatusBadge status={item.status} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
