"use client";

import { useEffect, useState } from "react";
import { ScrollText } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi, AuditEvent } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

export function LiveAuditLogsPage() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi
      .auditEvents()
      .then((page) => setItems(page.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading
        title="Audit logs"
        description="Review sensitive actions and system events in your workspace."
      />
      {error ? (
        <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}
      {loading ? (
        <p className="text-sm text-slate-500">Loading audit logs...</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={ScrollText}
          title="No audit logs yet"
          description="Audit logs will appear as your workspace is used."
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-4 font-medium">Action</th>
                <th className="px-5 py-4 font-medium">Actor</th>
                <th className="px-5 py-4 font-medium">Target</th>
                <th className="px-5 py-4 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-200">
                  <td className="px-5 py-4 font-medium text-slate-950">
                    {item.action_label}
                  </td>
                  <td className="px-5 py-4 text-slate-700">
                    {item.actor_display_name}
                  </td>
                  <td className="px-5 py-4 text-slate-700">
                    {item.target_label}
                  </td>
                  <td className="px-5 py-4 text-slate-500">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
