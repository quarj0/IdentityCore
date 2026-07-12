"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  buildOrganizationConfig,
  fetchOrganizationRecord,
  organizationRecordToAdminRecord,
} from "@/features/organizations/live-data";

type OrganizationDetailPageProps = {
  organizationId: string;
};

export function OrganizationDetailPage({
  organizationId,
}: OrganizationDetailPageProps) {
  const [config, setConfig] =
    useState<ReturnType<typeof buildOrganizationConfig> | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchOrganizationRecord(organizationId);
      if (!active || !data.organization) return;

      setConfig(
        buildOrganizationConfig(
          [organizationRecordToAdminRecord(data.organization)],
          data.supportingDocuments,
        ),
      );
    }

    void load();
    return () => {
      active = false;
    };
  }, [organizationId]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return <AdminDetailPage id={organizationId} config={resolvedConfig} />;
}
