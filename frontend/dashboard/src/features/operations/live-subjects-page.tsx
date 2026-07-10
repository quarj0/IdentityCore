"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, VerificationSubject } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveSubjectsPage() {
  const [items, setItems] = useState<VerificationSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi.subjects()
      .then((page) => setItems(page.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading title="Subjects" description="View people and entities that have gone through verification workflows." />
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {loading ? (
        <p className="text-sm text-slate-500">Loading subjects...</p>
      ) : items.length === 0 ? (
        <EmptyState icon={Users} title="No subjects yet" description="Subjects will appear after verification requests are created." />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-4 font-medium">Subject</th>
                <th className="px-5 py-4 font-medium">External reference</th>
                <th className="px-5 py-4 font-medium">Phone</th>
                <th className="px-5 py-4 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-200">
                  <td className="px-5 py-4">
                    <p className="font-medium text-slate-950">{item.full_name || item.email || item.id}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.email}</p>
                  </td>
                  <td className="px-5 py-4 text-slate-700">{item.external_reference || "None"}</td>
                  <td className="px-5 py-4 text-slate-700">{item.phone_number || "None"}</td>
                  <td className="px-5 py-4 text-slate-500">{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
