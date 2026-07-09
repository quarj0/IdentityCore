import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { AiProvider } from "@/features/ai-providers/mock-data";
import { AiProviderStatusPill } from "@/features/ai-providers/components/ai-provider-status-pill";

type AiProvidersTableProps = {
  providers: AiProvider[];
};

export function AiProvidersTable({ providers }: AiProvidersTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">Provider</th>
              <th className="px-5 py-4 font-medium">Status</th>
              <th className="px-5 py-4 font-medium">Type</th>
              <th className="px-5 py-4 font-medium">Latency</th>
              <th className="px-5 py-4 font-medium">Success rate</th>
              <th className="px-5 py-4 font-medium">Cost</th>
              <th className="px-5 py-4 font-medium">Priority</th>
              <th className="px-5 py-4 font-medium">Region</th>
              <th className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {providers.map((provider) => (
              <tr key={provider.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={`/ai-providers/${provider.id}`}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {provider.name}
                  </Link>
                  <p className="mt-1 text-xs text-slate-500">{provider.model}</p>
                </td>

                <td className="px-5 py-4">
                  <AiProviderStatusPill status={provider.status} />
                </td>

                <td className="px-5 py-4 capitalize text-slate-700">{provider.type}</td>
                <td className="px-5 py-4 text-slate-700">
                  {provider.latencyMs > 0 ? `${provider.latencyMs}ms` : "Paused"}
                </td>
                <td className="px-5 py-4 text-slate-700">{provider.successRate}</td>
                <td className="px-5 py-4 text-slate-700">{provider.costPerCheck}</td>
                <td className="px-5 py-4 text-slate-700">#{provider.priority}</td>
                <td className="px-5 py-4 text-slate-700">{provider.region}</td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/ai-providers/${provider.id}`}>View</Link>
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