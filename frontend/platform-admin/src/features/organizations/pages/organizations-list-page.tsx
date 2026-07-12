"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import {
  buildOrganizationConfig,
  fetchOrganizationRecords,
} from "@/features/organizations/live-data";

export function OrganizationsListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildOrganizationConfig>["records"]
  >([]);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchOrganizationRecords();
      if (active) {
        setRecords(data);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const config = useMemo(
    () => createAdminListConfig(buildOrganizationConfig(records)),
    [records],
  );

  return <AdminListPage config={config} />;
}
