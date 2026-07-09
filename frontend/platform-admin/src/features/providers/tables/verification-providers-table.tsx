import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { VerificationProvider } from "@/features/providers/mock-data";
import { VerificationProviderStatusPill } from "@/features/providers/components/verification-provider-status-pill";

type VerificationProvidersTableProps = {
  providers: VerificationProvider[];
};

export function VerificationProvidersTable({
  providers,
}: VerificationProvidersTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">Provider</th>
              <th className="px-5 py-4 font-medium">Status</th>
              <th className="px-5 py-4 font-medium">Category</th>
              <th className="px-5 py-4 font-medium">Countries</th>
              <th className="px-5 py-4 font-medium">Integration</th>
              <th className="px-5 py-4 font-medium">Volume</th>
              <th className="px-5 py-4 font-medium">Cost</th>
              <th className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {providers.map((provider) => (
              <tr key={provider.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={`/providers/${provider.id}`}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {provider.name}
                  </Link>
                  <p className="mt-1 text-xs text-slate-500">{provider.apiReadiness}</p>
                </td>

                <td className="px-5 py-4">
                  <VerificationProviderStatusPill status={provider.status} />
                </td>

                <td className="px-5 py-4 text-slate-700">{provider.category}</td>
                <td className="px-5 py-4 text-slate-700">{provider.countries.join(", ")}</td>
                <td className="px-5 py-4 text-slate-700">{provider.integrationStage}</td>
                <td className="px-5 py-4 text-slate-700">{provider.monthlyVolume.toLocaleString()}</td>
                <td className="px-5 py-4 text-slate-700">{provider.estimatedCost}</td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/providers/${provider.id}`}>View</Link>
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