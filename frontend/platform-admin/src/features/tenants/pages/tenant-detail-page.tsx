"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  buildTenantConfig,
  fetchTenantRecord,
  tenantRecordToAdminRecord,
} from "@/features/tenants/live-data";

type TenantDetailPageProps = {
  tenantId: string;
};

export function TenantDetailPage({ tenantId }: TenantDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildTenantConfig> | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const tenant = await fetchTenantRecord(tenantId);
      if (!active || !tenant) return;

      setConfig(buildTenantConfig([tenantRecordToAdminRecord(tenant)]));
    }

    void load();
    return () => {
      active = false;
    };
  }, [tenantId]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return <AdminDetailPage id={tenantId} config={resolvedConfig} />;
}
