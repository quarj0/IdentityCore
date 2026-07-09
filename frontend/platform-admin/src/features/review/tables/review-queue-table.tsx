import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { ReviewCase } from "@/features/review/mock-data";
import { ReviewCaseStatusPill } from "@/features/review/components/review-case-status-pill";

type ReviewQueueTableProps = {
  cases: ReviewCase[];
};

export function ReviewQueueTable({ cases }: ReviewQueueTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1150px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">Case</th>
              <th className="px-5 py-4 font-medium">Status</th>
              <th className="px-5 py-4 font-medium">Organization</th>
              <th className="px-5 py-4 font-medium">Country</th>
              <th className="px-5 py-4 font-medium">Risk</th>
              <th className="px-5 py-4 font-medium">Assigned</th>
              <th className="px-5 py-4 font-medium">SLA</th>
              <th className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {cases.map((reviewCase) => (
              <tr key={reviewCase.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={`/review/${reviewCase.id}`}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {reviewCase.applicantName}
                  </Link>
                  <p className="mt-1 text-xs text-slate-500">
                    {reviewCase.id} · {reviewCase.documentType}
                  </p>
                </td>

                <td className="px-5 py-4">
                  <ReviewCaseStatusPill status={reviewCase.status} />
                </td>

                <td className="px-5 py-4 text-slate-700">
                  {reviewCase.organizationName}
                </td>

                <td className="px-5 py-4 text-slate-700">{reviewCase.country}</td>

                <td className="px-5 py-4">
                  <span className="font-medium text-slate-950">
                    {reviewCase.riskScore}
                  </span>
                  <p className="mt-1 text-xs capitalize text-slate-500">
                    {reviewCase.priority}
                  </p>
                </td>

                <td className="px-5 py-4 text-slate-700">{reviewCase.assignedTo}</td>
                <td className="px-5 py-4 text-slate-700">{reviewCase.slaDueAt}</td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/review/${reviewCase.id}`}>Review</Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}