"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildApiClientConfig,
  fetchApiClientRecords,
} from "@/features/api-clients/live-data";

export function ApiClientsListPage() {
  const [records, setRecords] = useState<ReturnType<typeof buildApiClientConfig>["records"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchApiClientRecords();
        if (active) {
          setRecords(data);
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load API clients.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading && records.length === 0) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="API clients"
          title="Loading API clients"
          description="Fetching live API client records from the backend."
        />
      </div>
    );
  }

  if (error && records.length === 0) {
    return <EmptyState title="Unable to load API clients" description={error} />;
  }

  return <AdminListPage config={buildApiClientConfig(records)} />;
}
