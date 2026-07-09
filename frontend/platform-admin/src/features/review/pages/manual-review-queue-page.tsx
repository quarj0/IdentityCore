"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { reviewCases } from "@/features/review/mock-data";
import { ReviewQueueTable } from "@/features/review/tables/review-queue-table";

export function ManualReviewQueuePage() {
  const [query, setQuery] = useState("");

  const filteredCases = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) return reviewCases;

    return reviewCases.filter((reviewCase) =>
      [
        reviewCase.id,
        reviewCase.applicantName,
        reviewCase.organizationName,
        reviewCase.status,
        reviewCase.country,
        reviewCase.documentType,
        reviewCase.priority,
        reviewCase.assignedTo,
        reviewCase.failureReason,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Human review operations"
        title="Manual Review Queue"
        description="Manage global review cases, reviewer assignment, escalations, quality control and reviewer performance."
        actions={
          <>
            <Button variant="outline">Export queue</Button>
            <Button>Bulk assign</Button>
          </>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search review cases..."
              className="pl-10"
              aria-label="Search review cases"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Status</Button>
            <Button variant="outline">Priority</Button>
            <Button variant="outline">Reviewer</Button>
            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredCases.length > 0 ? (
        <ReviewQueueTable cases={filteredCases} />
      ) : (
        <EmptyState
          title="No review cases found"
          description="No review case matches the current search or filters."
        />
      )}
    </div>
  );
}