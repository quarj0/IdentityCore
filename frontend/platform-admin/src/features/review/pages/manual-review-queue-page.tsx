"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Filter, Search, RefreshCcw } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { StatusPill } from "@/components/shared/status-pill";
import {
  fetchOrganizationReviewQueue,
  type OrganizationReviewItem,
} from "@/features/review/review-api";

function formatDateTime(value: string | null) {
  if (!value) return "Pending";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function reviewStatusTone(status: string) {
  if (status === "approved") return "success";
  if (status === "needs_information") return "warning";
  if (status === "rejected") return "danger";
  if (status === "changed_after_approval") return "info";
  return "neutral";
}

function buildSearchIndex(item: OrganizationReviewItem) {
  return [
    item.organizationId,
    item.organizationName,
    item.organizationSlug,
    item.organizationStatus,
    item.tenantStatus,
    item.organizationVerificationReviewStatus,
    item.organizationVerificationReviewNote,
    item.organizationVerificationSubmittedAt,
    item.organizationType,
    item.organizationCountry,
    item.organizationCountryName,
    item.administratorFullName,
    item.administratorEmail,
    item.businessRegistrationNumber,
    item.taxIdentificationNumber,
    item.registeredAddress,
    item.officialWebsite,
    item.reviewPriority,
    item.reviewSummary,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function ManualReviewQueuePage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<OrganizationReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadQueue() {
      setLoading(true);
      setError(null);

      try {
        const queue = await fetchOrganizationReviewQueue();
        if (!active) return;
        setItems(queue);
      } catch (loadError) {
        if (!active) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unable to load organization review queue.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadQueue();
    return () => {
      active = false;
    };
  }, [refreshTick]);

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return items;
    return items.filter((item) => buildSearchIndex(item).includes(normalizedQuery));
  }, [items, query]);

  const pendingCount = items.filter(
    (item) =>
      item.organizationVerificationReviewStatus === "submitted" ||
      item.organizationVerificationReviewStatus === "changed_after_approval",
  ).length;
  const needsInfoCount = items.filter(
    (item) => item.organizationVerificationReviewStatus === "needs_information",
  ).length;
  const changedCount = items.filter(
    (item) => item.organizationVerificationChangedAfterApproval,
  ).length;

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform admin review"
        title="Organization Review Queue"
        description="Review submitted organization evidence, approve changes, or request more information before production access is finalized."
        actions={
          <>
            <Button
              variant="outline"
              onClick={() => setRefreshTick((value) => value + 1)}
              disabled={loading}
            >
              <RefreshCcw className="mr-2 size-4" />
              Refresh
            </Button>
            <Button variant="outline">Export queue</Button>
          </>
        }
      />

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Queued items</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">
            {loading ? "..." : pendingCount}
          </p>
          <p className="mt-1 text-sm text-slate-500">Loaded from the backend queue</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Needs information</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{needsInfoCount}</p>
          <p className="mt-1 text-sm text-slate-500">Requires a resubmission</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Changed after approval</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{changedCount}</p>
          <p className="mt-1 text-sm text-slate-500">Returned to review after edits</p>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search organization reviews..."
              className="pl-10"
              aria-label="Search organization reviews"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">
              <Filter className="mr-2 size-4" />
              Filters
            </Button>
            <Button variant="outline">Pending</Button>
            <Button variant="outline">Changed after approval</Button>
          </div>
        </div>
      </section>

      {error ? (
        <EmptyState
          title="Unable to load the queue"
          description={error}
          action={
            <Button onClick={() => setRefreshTick((value) => value + 1)}>
              Try again
            </Button>
          }
        />
      ) : filteredItems.length > 0 ? (
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-275 text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-4 font-medium">Organization</th>
                  <th className="px-5 py-4 font-medium">Review</th>
                  <th className="px-5 py-4 font-medium">Status</th>
                  <th className="px-5 py-4 font-medium">Submitted</th>
                  <th className="px-5 py-4 font-medium">Reviewer note</th>
                  <th className="px-5 py-4 text-right font-medium">Actions</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200">
                {filteredItems.map((item) => (
                  <tr key={item.organizationId} className="transition hover:bg-slate-50">
                    <td className="px-5 py-4">
                      <Link
                        href={`/review/${item.organizationId}`}
                        className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                      >
                        {item.organizationName}
                      </Link>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.organizationCountryName} · {item.organizationType} ·{" "}
                        {item.organizationSlug}
                      </p>
                    </td>

                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-2">
                        <StatusPill tone={reviewStatusTone(item.organizationVerificationReviewStatus)}>
                          {item.organizationVerificationReviewStatus.replace(/_/g, " ")}
                        </StatusPill>
                        {item.organizationVerificationChangedAfterApproval ? (
                          <StatusPill tone="info">changed after approval</StatusPill>
                        ) : null}
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      <p className="font-medium text-slate-950">{item.organizationStatus}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.tenantStatus}</p>
                    </td>

                    <td className="px-5 py-4 text-slate-700">
                      {formatDateTime(item.organizationVerificationSubmittedAt)}
                    </td>

                    <td className="px-5 py-4 text-slate-700">
                      <p className="max-w-70 truncate">
                        {item.organizationVerificationReviewNote || "No note recorded yet."}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Priority: {item.reviewPriority ?? "normal"}
                      </p>
                    </td>

                    <td className="px-5 py-4 text-right">
                      <Button asChild variant="outline" size="sm">
                        <Link href={`/review/${item.organizationId}`}>Review</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No organization reviews found"
          description="No submitted organization verifications match the current search or filters."
        />
      )}
    </div>
  );
}
