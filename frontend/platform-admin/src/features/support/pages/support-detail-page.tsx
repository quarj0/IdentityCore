"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildSupportConfig,
  fetchSupportRecord,
  supportRecordToAdminRecord,
} from "@/features/support/live-data";

type SupportDetailPageProps = {
  ticketId: string;
};

export function SupportDetailPage({ ticketId }: SupportDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSupportRecord(ticketId);
        if (active && data) setRecord(supportRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load support ticket.",
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
  }, [ticketId]);

  const config = useMemo(() => buildSupportConfig(record ? [record] : []), [record]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Support" title="Support ticket" description="Live support data." />
        <EmptyState title="Support ticket unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Support"
        title="Loading support ticket"
        description="Fetching support data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Support ticket not found"
        description="This support ticket may have been resolved or removed."
      />
    );
  }

  return <AdminDetailPage id={ticketId} config={config} />;
}
