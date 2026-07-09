"use client";

import { useState } from "react";
import { Button } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { mockNotifications } from "@/mock";

export default function NotificationsPage() {
  const [filter, setFilter] = useState("All");

  const notifications = mockNotifications.filter((item) =>
    filter === "All" ? true : item.status === filter,
  );

  return (
    <div className="space-y-8">
      <PageHeading
        title="Notifications"
        description="Review workspace alerts, reminders, and product updates."
        action={<Button className="rounded-xl">Mark all read</Button>}
      />

      <div className="flex flex-wrap gap-2">
        {["All", "Unread", "Read"].map((item) => (
          <button
            key={item}
            onClick={() => setFilter(item)}
            className={
              filter === item
                ? "rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white"
                : "rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600"
            }
          >
            {item}
          </button>
        ))}
      </div>

      <div className="grid gap-3">
        {notifications.map((item) => (
          <div
            key={item.id}
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">{item.title}</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {item.description}
                </p>
                <p className="mt-2 text-xs text-slate-400">{item.time}</p>
              </div>

              <StatusBadge status={item.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
