"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildWebhookConfig,
  fetchWebhookRecord,
  webhookEndpointToRecord,
} from "@/features/webhooks/live-data";

type WebhookDetailPageProps = {
  webhookId: string;
};

export function WebhookDetailPage({ webhookId }: WebhookDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildWebhookConfig> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);

      try {
        const endpoint = await fetchWebhookRecord(webhookId);
        if (!active) return;
        setConfig(buildWebhookConfig([webhookEndpointToRecord(endpoint)]));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load webhook endpoint.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [webhookId]);

  if (error) {
    return <EmptyState title="Unable to load webhook" description={error} />;
  }

  if (!config) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="Webhooks"
          title="Loading webhook"
          description="Fetching the live webhook endpoint from the backend."
        />
      </div>
    );
  }

  return <AdminDetailPage id={webhookId} config={config} />;
}
