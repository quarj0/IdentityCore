"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildSecurityConfig,
  fetchSecurityRecord,
  securityRecordToAdminRecord,
} from "@/features/security/live-data";

type SecurityDetailPageProps = {
  securityId: string;
};

export function SecurityDetailPage({ securityId }: SecurityDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSecurityRecord(securityId);
        if (active && data) setRecord(securityRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load security record.",
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
  }, [securityId]);

  const config = useMemo(() => buildSecurityConfig(record ? [record] : []), [record]);

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Security" title="Security record" description="Live security data." />
        <EmptyState title="Security record unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Security"
        title="Loading security record"
        description="Fetching security data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Security record not found"
        description="This security case may have been resolved or removed."
      />
    );
  }

  return <AdminDetailPage id={securityId} config={config} />;
}
