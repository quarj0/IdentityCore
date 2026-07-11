"use client";
import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/dashboard-api";

export function ApprovalBanner() {
  const [status, setStatus] = useState("");
  useEffect(() => { dashboardApi.organization().then((organization) => setStatus(organization.status)).catch(() => undefined); }, []);
  if (!status || status === "active") return null;
  return <div className="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 sm:px-6 lg:px-8">
    <strong>Platform approval pending.</strong> You can explore the dashboard and use sandbox tools; production actions remain read-only until approval.
  </div>;
}
