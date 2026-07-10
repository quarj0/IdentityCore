"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardApi, Notification } from "@/lib/dashboard-api";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export function LiveNotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    dashboardApi.notifications()
      .then((response) => setItems(response.results))
      .catch((caught) => setError(messageOf(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <PageHeading title="Notifications" description="Review workspace alerts, reminders, and delivery events." />
      {error ? <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {loading ? (
        <p className="text-sm text-slate-500">Loading notifications...</p>
      ) : items.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications yet" description="Notification delivery records will appear here." />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-slate-950">{item.subject || item.template_code || item.channel}</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.body_preview || item.recipient}</p>
                  <p className="mt-2 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p>
                </div>
                <StatusBadge status={item.status} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
