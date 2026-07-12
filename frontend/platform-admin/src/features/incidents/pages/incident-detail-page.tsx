"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildIncidentConfig,
  fetchIncidentRecord,
  incidentRecordToAdminRecord,
} from "@/features/incidents/live-data";

type IncidentDetailPageProps = {
  incidentId: string;
};

export function IncidentDetailPage({ incidentId }: IncidentDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchIncidentRecord(incidentId);
        if (active && data) setRecord(incidentRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load incident record.",
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
  }, [incidentId]);

  const config = useMemo(() => buildIncidentConfig(record ? [record] : []), [record]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Incidents" title="Incident record" description="Live incident data." />
        <EmptyState title="Incident record unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Incidents"
        title="Loading incident record"
        description="Fetching incident data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Incident record not found"
        description="This incident may have been resolved or removed."
      />
    );
  }

  return <AdminDetailPage id={incidentId} config={config} />;
}
