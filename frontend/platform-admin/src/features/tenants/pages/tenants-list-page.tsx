"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { buildTenantConfig, fetchTenantRecords } from "@/features/tenants/live-data";

export function TenantsListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildTenantConfig>["records"]
  >([]);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchTenantRecords();
      if (active) {
        setRecords(data);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const config = useMemo(() => createAdminListConfig(buildTenantConfig(records)), [records]);

  return <AdminListPage config={config} />;
}
