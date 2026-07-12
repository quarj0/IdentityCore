 "use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildAnalyticsConfig,
  fetchAnalyticsRecords,
} from "@/features/analytics/live-data";

export function AnalyticsListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAnalyticsRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load analytics.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const config = useMemo(() => buildAnalyticsConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Analytics" title="Analytics" description="Live analytics dashboards." />
        <EmptyState title="Unable to load analytics" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Analytics"
        title="Loading analytics"
        description="Fetching analytics dashboards from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
