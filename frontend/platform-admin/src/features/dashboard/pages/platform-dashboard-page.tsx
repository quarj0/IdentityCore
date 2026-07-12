"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@identitycore/ui";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { EmptyState } from "@/components/feedback/empty-state";
import { fetchOrganizationReviewQueue } from "@/features/review/review-api";
import { AlertTriangle, RefreshCcw, ShieldCheck, FileCheck2 } from "lucide-react";

function statusLabel(status: string) {
  return status.replace(/_/g, " ");
}

export function PlatformDashboardPage() {
  const [queued, setQueued] = useState(0);
  const [needsInformation, setNeedsInformation] = useState(0);
  const [changedAfterApproval, setChangedAfterApproval] = useState(0);
  const [latestReview, setLatestReview] = useState<{
    organizationName: string;
    status: string;
    note: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);
      try {
        const queue = await fetchOrganizationReviewQueue(20);
        if (!active) return;

        setQueued(queue.length);
        setNeedsInformation(
          queue.filter(
            (item) => item.organizationVerificationReviewStatus === "needs_information",
          ).length,
        );
        setChangedAfterApproval(
          queue.filter((item) => item.organizationVerificationChangedAfterApproval).length,
        );
        const latest = queue[0];
        setLatestReview(
          latest
            ? {
                organizationName: latest.organizationName,
                status: latest.organizationVerificationReviewStatus,
                note: latest.organizationVerificationReviewNote,
              }
            : null,
        );
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load the review queue.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [refreshTick]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform command center"
        title="Platform Dashboard"
        description="Track the live organization review queue and move into the internal console for approvals, rejections, and additional information requests."
        actions={
          <Button
            variant="outline"
            onClick={() => setRefreshTick((value) => value + 1)}
          >
            <RefreshCcw className="mr-2 size-4" />
            Refresh
          </Button>
        }
      />

      {error ? (
        <EmptyState
          title="Unable to load platform summary"
          description={error}
          action={
            <Button onClick={() => setRefreshTick((value) => value + 1)}>
              Try again
            </Button>
          }
        />
      ) : null}

      <section className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Queued reviews"
          value={queued.toString()}
          change="Live review queue"
          trend="neutral"
          helperText="organization reviews"
          icon={FileCheck2}
        />
        <MetricCard
          label="Needs information"
          value={needsInformation.toString()}
          change="Needs resubmission"
          trend="neutral"
          helperText="review state"
          icon={AlertTriangle}
        />
        <MetricCard
          label="Changed after approval"
          value={changedAfterApproval.toString()}
          change="Returned to review"
          trend="neutral"
          helperText="re-review state"
          icon={ShieldCheck}
        />
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Latest review item</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-950">
              {latestReview ? latestReview.organizationName : "No queued reviews"}
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              {latestReview
                ? `Status: ${statusLabel(latestReview.status)}`
                : "New organization submissions will appear here once they reach the review queue."}
            </p>
          </div>

          <Button asChild>
            <Link href="/review">Open review queue</Link>
          </Button>
        </div>

        {latestReview ? (
          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Review note</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {latestReview.note || "No reviewer note captured yet."}
            </p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
