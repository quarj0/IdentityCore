"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminRecord } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildBillingConfig,
  fetchBillingRecords,
} from "@/features/billing/live-data";

export function BillingListPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchBillingRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load billing records.",
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

  const config = useMemo(() => buildBillingConfig(records), [records]);

  if (error) {
    return (
      <>
        <PageHeader
          eyebrow="Billing"
          title="Billing"
          description="Manage organizations, invoices, subscriptions, usage, revenue and platform fees."
        />
        <EmptyState title="Unable to load billing records" description={error} />
      </>
    );
  }

  if (loading && !records.length) {
    return (
      <PageHeader
        eyebrow="Billing"
        title="Loading billing records"
        description="Fetching billing data from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
