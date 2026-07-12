"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildSupportConfig,
  fetchSupportRecords,
} from "@/features/support/live-data";

export function SupportListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSupportRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error ? loadError.message : "Unable to load support tickets.",
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

  const config = useMemo(() => buildSupportConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Support" title="Support" description="Live support tickets." />
        <EmptyState title="Unable to load support tickets" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Support"
        title="Loading support tickets"
        description="Fetching support data from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
