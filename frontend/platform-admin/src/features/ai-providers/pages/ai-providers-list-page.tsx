"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import {
  buildAiProviderConfig,
  fetchAiProviderRecords,
} from "@/features/ai-providers/live-data";

export function AiProvidersListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildAiProviderConfig>["records"]
  >([]);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchAiProviderRecords();
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
    () => createAdminListConfig(buildAiProviderConfig(records)),
    [records],
  );

  return <AdminListPage config={config} />;
}
