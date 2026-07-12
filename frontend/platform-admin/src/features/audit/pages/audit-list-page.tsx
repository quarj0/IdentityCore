"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import { buildAuditConfig, fetchAuditRecords } from "@/features/audit/live-data";

export function AuditListPage() {
  const [records, setRecords] = useState<ReturnType<typeof buildAuditConfig>["records"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchAuditRecords();
        if (active) {
          setRecords(data);
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load audit events.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading && records.length === 0) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="Platform audit"
          title="Loading audit"
          description="Fetching the live audit trail from the backend."
        />
      </div>
    );
  }

  if (error && records.length === 0) {
    return (
      <EmptyState
        title="Unable to load audit events"
        description={error}
      />
    );
  }

  const config = createAdminListConfig(buildAuditConfig(records));

  return <AdminListPage config={config} />;
}
