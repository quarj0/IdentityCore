"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  buildProvidersConfig,
  fetchVerificationProviderRecord,
} from "@/features/providers/live-data";

type VerificationProviderDetailPageProps = {
  providerId: string;
};

export function VerificationProviderDetailPage({
  providerId,
}: VerificationProviderDetailPageProps) {
  const [recordId, setRecordId] = useState<string | null>(null);
  const [config, setConfig] =
    useState<ReturnType<typeof buildProvidersConfig> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);
      try {
        const provider = await fetchVerificationProviderRecord(providerId);
        if (!active) return;
        const record = {
          id: provider.id,
          title: provider.name,
          subtitle: `${provider.provider_type.replace(/_/g, " ")} · ${provider.code}`,
          status: provider.status,
          statusTone:
            provider.status === "active"
              ? "success"
              : provider.status === "testing"
                ? "warning"
                : provider.status === "disabled"
                  ? "danger"
                  : provider.status === "deprecated"
                    ? "neutral"
                    : "info",
          primaryMeta: provider.provider_type,
          secondaryMeta: provider.code,
          tertiaryMeta: `Config keys: ${Object.keys(provider.configuration || {}).length}`,
          owner: "Platform admin",
          updatedAt: provider.updated_at,
          href: `/providers/${provider.id}`,
        } as const;
        setRecordId(record.id);
        setConfig(buildProvidersConfig([record]));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load this verification provider.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [providerId]);

  if (error) {
    return <EmptyState title="Verification provider unavailable" description={error} />;
  }

  if (!config || !recordId) {
    return (
      <EmptyState
        title="Loading verification provider"
        description="Fetching live provider details from the backend."
      />
    );
  }

  return <AdminDetailPage id={recordId} config={config} />;
}
