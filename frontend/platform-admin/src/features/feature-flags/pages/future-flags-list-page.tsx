"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildFeatureFlagConfig,
  fetchFeatureFlagRecords,
} from "@/features/feature-flags/live-data";

export function FeatureFlagsListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchFeatureFlagRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error ? loadError.message : "Unable to load feature flags.",
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

  const config = useMemo(() => buildFeatureFlagConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Feature flags" title="Feature Flags" description="Live release controls." />
        <EmptyState title="Unable to load feature flags" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Feature flags"
        title="Loading feature flags"
        description="Fetching feature flags from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
