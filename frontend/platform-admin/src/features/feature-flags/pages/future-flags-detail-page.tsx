"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildFeatureFlagConfig,
  fetchFeatureFlagRecord,
  featureFlagRecordToAdminRecord,
} from "@/features/feature-flags/live-data";

type FeatureFlagDetailPageProps = {
  flagId: string;
};

export function FeatureFlagDetailPage({ flagId }: FeatureFlagDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchFeatureFlagRecord(flagId);
        if (active && data) setRecord(featureFlagRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load feature flag.",
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
  }, [flagId]);

  const config = useMemo(() => buildFeatureFlagConfig(record ? [record] : []), [record]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Feature flags" title="Feature flag" description="Live release control data." />
        <EmptyState title="Feature flag unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Feature flags"
        title="Loading feature flag"
        description="Fetching feature flag data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Feature flag not found"
        description="This feature flag may have been removed or is unavailable."
      />
    );
  }

  return <AdminDetailPage id={flagId} config={config} />;
}
