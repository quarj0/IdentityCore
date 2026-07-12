"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import {
  buildPlatformAdminConfig,
  fetchPlatformAdminRecords,
} from "@/features/users/live-data";

export function UsersListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildPlatformAdminConfig>["records"]
  >([]);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchPlatformAdminRecords();
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
    () => createAdminListConfig(buildPlatformAdminConfig(records)),
    [records],
  );

  return <AdminListPage config={config} />;
}
