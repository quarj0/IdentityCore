"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildIncidentConfig,
  fetchIncidentRecords,
} from "@/features/incidents/live-data";

export function IncidentsListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchIncidentRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error ? loadError.message : "Unable to load incidents.",
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

  const config = useMemo(() => buildIncidentConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Incidents" title="Incidents" description="Live platform incidents." />
        <EmptyState title="Unable to load incidents" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Incidents"
        title="Loading incidents"
        description="Fetching incidents from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
