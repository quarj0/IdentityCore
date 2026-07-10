"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { DashboardUser, dashboardApi } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveTeamPage() {
  const [items, setItems] = useState<DashboardUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi.team()
      .then((response) => setItems(response.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading title="Team" description="Review workspace members, status, and assigned roles." />
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {loading ? (
        <p className="text-sm text-slate-500">Loading team members...</p>
      ) : items.length === 0 ? (
        <EmptyState icon={Users} title="No team members" description="Workspace members will appear here after they are created." />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-4 font-medium">Member</th>
                <th className="px-5 py-4 font-medium">Roles</th>
                <th className="px-5 py-4 font-medium">MFA</th>
                <th className="px-5 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.public_id} className="border-t border-slate-200">
                  <td className="px-5 py-4">
                    <p className="font-medium text-slate-950">{`${item.first_name} ${item.last_name}`.trim() || item.email}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.email}</p>
                  </td>
                  <td className="px-5 py-4 text-slate-700">{item.roles.join(", ") || "Member"}</td>
                  <td className="px-5 py-4 text-slate-700">{item.mfa_enabled ? "Enabled" : "Not enabled"}</td>
                  <td className="px-5 py-4"><StatusBadge status={item.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
