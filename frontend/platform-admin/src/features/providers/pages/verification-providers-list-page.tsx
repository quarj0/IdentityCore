"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import type { AdminModuleConfig } from "@/components/admin-module/admin-module-types";
import { PageHeader } from "@/components/shared/page-header";
import { fetchVerificationProviderRecords } from "@/features/providers/live-data";

export function VerificationProvidersListPage() {
  const [records, setRecords] = useState<AdminModuleConfig["records"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchVerificationProviderRecords();
        if (active) setRecords(data);
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load verification providers.",
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

  const config = useMemo<AdminModuleConfig | null>(() => {
    if (!records.length) return null;
    return {
      moduleLabel: "Verification providers",
      listTitle: "Verification Providers",
      listDescription:
        "Manage provider registry entries used by the platform-admin operations console.",
      detailBreadcrumbLabel: "Verification Providers",
      searchPlaceholder: "Search verification providers...",
      createLabel: "Add provider",
      exportLabel: "Export",
      filters: ["Status", "Type", "Owner"],
      records,
      getRecord: (id) => records.find((record) => record.id === id),
      getMetrics: (record) => [
        { label: "Type", value: record.primaryMeta, helper: "provider class" },
        { label: "Code", value: record.secondaryMeta, helper: "registry code" },
        { label: "Config", value: record.tertiaryMeta, helper: "settings" },
        { label: "Updated", value: record.updatedAt, helper: "backend" },
      ],
      getSections: (record) => [
        {
          title: "Provider record",
          description: "Backend provider registry details.",
          items: [
            { label: "Name", value: record.title },
            { label: "Status", value: record.status },
            { label: "Last updated", value: record.updatedAt },
          ],
        },
      ],
    };
  }, [records]);

  if (error) {
    return (
      <>
        <PageHeader
          eyebrow="Verification providers"
          title="Verification Providers"
          description="Manage provider registry entries used by the platform-admin operations console."
        />
        <EmptyState title="Unable to load verification providers" description={error} />
      </>
    );
  }

  if (loading || !config) {
    return (
      <PageHeader
        eyebrow="Verification providers"
        title="Loading verification providers"
        description="Fetching provider registry data from the backend."
      />
    );
  }

  return <AdminListPage config={config} />;
}
