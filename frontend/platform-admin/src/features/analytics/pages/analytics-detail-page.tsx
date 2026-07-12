 "use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  analyticsRecordToAdminRecord,
  buildAnalyticsConfig,
  fetchAnalyticsRecord,
} from "@/features/analytics/live-data";

type AnalyticsDetailPageProps = {
  analyticsId: string;
};

export function AnalyticsDetailPage({ analyticsId }: AnalyticsDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAnalyticsRecord(analyticsId);
        if (active && data) setRecord(analyticsRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load analytics record.",
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
  }, [analyticsId]);

  const config = useMemo(() => buildAnalyticsConfig(record ? [record] : []), [record]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Analytics" title="Analytics record" description="Live analytics data." />
        <EmptyState title="Analytics record unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Analytics"
        title="Loading analytics record"
        description="Fetching analytics data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Analytics record not found"
        description="This analytics dashboard may have been removed or is unavailable."
      />
    );
  }

  return <AdminDetailPage id={analyticsId} config={config} />;
}
