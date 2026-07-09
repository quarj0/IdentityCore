import Link from "next/link";
import { Button } from "@identitycore/ui";
import { StatusPill } from "@/components/shared/status-pill";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";

type AdminRecordTableProps = {
  records: AdminRecord[];
};

export function AdminRecordTable({ records }: AdminRecordTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1080px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">Name</th>
              <th className="px-5 py-4 font-medium">Status</th>
              <th className="px-5 py-4 font-medium">Primary</th>
              <th className="px-5 py-4 font-medium">Secondary</th>
              <th className="px-5 py-4 font-medium">Tertiary</th>
              <th className="px-5 py-4 font-medium">Owner</th>
              <th className="px-5 py-4 font-medium">Updated</th>
              <th className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {records.map((record) => (
              <tr key={record.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={record.href}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {record.title}
                  </Link>
                  <p className="mt-1 max-w-md text-xs text-slate-500">
                    {record.subtitle}
                  </p>
                </td>

                <td className="px-5 py-4">
                  <StatusPill tone={record.statusTone}>{record.status}</StatusPill>
                </td>

                <td className="px-5 py-4 text-slate-700">{record.primaryMeta}</td>
                <td className="px-5 py-4 text-slate-700">{record.secondaryMeta}</td>
                <td className="px-5 py-4 text-slate-700">{record.tertiaryMeta}</td>
                <td className="px-5 py-4 text-slate-700">{record.owner}</td>
                <td className="px-5 py-4 text-slate-500">{record.updatedAt}</td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={record.href}>View</Link>
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