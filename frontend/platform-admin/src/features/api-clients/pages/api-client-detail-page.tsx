"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { PageHeader } from "@/components/shared/page-header";
import {
  apiClientToRecord,
  buildApiClientConfig,
  fetchApiClientRecord,
} from "@/features/api-clients/live-data";

type ApiClientDetailPageProps = {
  clientId: string;
};

export function ApiClientDetailPage({ clientId }: ApiClientDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildApiClientConfig> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);

      try {
        const client = await fetchApiClientRecord(clientId);
        if (!active) return;
        setConfig(buildApiClientConfig([apiClientToRecord(client)]));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load API client.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [clientId]);

  if (error) {
    return <EmptyState title="Unable to load API client" description={error} />;
  }

  if (!config) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="API clients"
          title="Loading API client"
          description="Fetching the live API client from the backend."
        />
      </div>
    );
  }

  return <AdminDetailPage id={clientId} config={config} />;
}
