"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildBillingConfig,
  fetchBillingRecord,
  billingRecordToAdminRecord,
} from "@/features/billing/live-data";

type BillingDetailPageProps = {
  billingId: string;
};

export function BillingDetailPage({ billingId }: BillingDetailPageProps) {
  const [record, setRecord] = useState<AdminRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchBillingRecord(billingId);
        if (active && data) setRecord(billingRecordToAdminRecord(data));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load billing record.",
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
  }, [billingId]);

  const config = useMemo(
    () => buildBillingConfig(record ? [record] : []),
    [record],
  );

  if (error) {
    return (
      <>
        <PageHeader eyebrow="Billing" title="Billing record" description="Live billing data." />
        <EmptyState title="Billing record unavailable" description={error} />
      </>
    );
  }

  if (loading && !record) {
    return (
      <PageHeader
        eyebrow="Billing"
        title="Loading billing record"
        description="Fetching billing data from the backend."
      />
    );
  }

  if (!record) {
    return (
      <EmptyState
        title="Billing record not found"
        description="This billing record may have been removed or is not available in the backend."
      />
    );
  }

  return <AdminDetailPage id={billingId} config={config} />;
}
