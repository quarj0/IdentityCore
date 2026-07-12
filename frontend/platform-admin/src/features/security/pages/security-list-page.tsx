"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildSecurityConfig,
  fetchSecurityRecords,
} from "@/features/security/live-data";

export function SecurityListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSecurityRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load security records.",
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

  const config = useMemo(() => buildSecurityConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Security" title="Security" description="Live security cases." />
        <EmptyState title="Unable to load security records" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Security"
        title="Loading security records"
        description="Fetching security cases from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
