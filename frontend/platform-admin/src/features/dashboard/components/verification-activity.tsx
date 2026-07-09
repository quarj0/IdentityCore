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
          className="border-slate-200 bg-white/5 text-slate-200 hover:bg-white/10"
        >
          Export
        </Button>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-180 text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="pb-3 font-medium">
                Country
              </th>
              <th scope="col" className="pb-3 font-medium">
                Total
              </th>
              <th scope="col" className="pb-3 font-medium">
                Approved
              </th>
              <th scope="col" className="pb-3 font-medium">
                Failed
              </th>
              <th scope="col" className="pb-3 font-medium">
                Manual review
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-white/10">
            {verificationActivity.map((row) => (
              <tr key={row.country}>
                <td className="py-4 font-medium text-white">{row.country}</td>
                <td className="py-4 text-slate-300">{row.total}</td>
                <td className="py-4 text-emerald-300">{row.approved}</td>
                <td className="py-4 text-rose-300">{row.failed}</td>
                <td className="py-4 text-amber-300">{row.manualReview}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}
