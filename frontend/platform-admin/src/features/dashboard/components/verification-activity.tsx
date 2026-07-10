import { Button } from "@identitycore/ui";
import { SectionCard } from "@/components/shared/section-card";
import { verificationActivity } from "@/features/dashboard/mock-data";

export function VerificationActivity() {
  return (
    <SectionCard
      title="Verification activity"
      description="Global verification volume by country."
      action={
        <Button
          variant="outline"
          className="border-slate-200 bg-white text-slate-950 hover:bg-slate-100"
        >
          Export
        </Button>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-180 text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="pb-3 font-medium text-slate-700">
                Country
              </th>
              <th scope="col" className="pb-3 font-medium text-slate-700">
                Total
              </th>
              <th scope="col" className="pb-3 font-medium text-slate-700">
                Approved
              </th>
              <th scope="col" className="pb-3 font-medium text-slate-700">
                Failed
              </th>
              <th scope="col" className="pb-3 font-medium text-slate-700">
                Manual review
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {verificationActivity.map((row) => (
              <tr key={row.country}>
                <td className="py-4 font-medium text-slate-950">
                  {row.country}
                </td>
                <td className="py-4 text-slate-700">{row.total}</td>
                <td className="py-4 text-emerald-700">{row.approved}</td>
                <td className="py-4 text-rose-700">{row.failed}</td>
                <td className="py-4 text-amber-700">{row.manualReview}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}
