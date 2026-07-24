"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import {
  buildPlatformAdminConfig,
  fetchPlatformAdminRecords,
} from "@/features/users/live-data";
import { InviteAdminDialog } from "@/features/users/components/invite-admin-dialog";

export function UsersListPage() {
  const [records, setRecords] = useState<
    ReturnType<typeof buildPlatformAdminConfig>["records"]
  >([]);
  const [refreshToken, setRefreshToken] = useState(0);

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
  }, [refreshToken]);

  const config = useMemo(
    () => ({
      ...createAdminListConfig(buildPlatformAdminConfig(records)),
      headerActions: (
        <InviteAdminDialog onInvited={() => setRefreshToken((value) => value + 1)} />
      ),
    }),
    [records],
  );

  return <AdminListPage config={config} />;
}
