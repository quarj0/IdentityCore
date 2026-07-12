"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { buildSettingsConfig, fetchSettingsRecords } from "@/features/settings/live-data";

export function SettingsListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildSettingsConfig>["records"]
  >([]);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchSettingsRecords();
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
    () => createAdminListConfig(buildSettingsConfig(records)),
    [records],
  );

  return <AdminListPage config={config} />;
}
