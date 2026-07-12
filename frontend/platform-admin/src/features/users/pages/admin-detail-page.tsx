"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage as ModuleDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  adminUserToAdminRecord,
  buildPlatformAdminConfig,
  fetchPlatformAdminRecord,
} from "@/features/users/live-data";

type AdminDetailPageProps = {
  userId: string;
};

export function AdminDetailPage({ userId }: AdminDetailPageProps) {
  const [config, setConfig] =
    useState<ReturnType<typeof buildPlatformAdminConfig> | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const user = await fetchPlatformAdminRecord(userId);
      if (!active || !user) return;

      setConfig(buildPlatformAdminConfig([adminUserToAdminRecord(user)]));
    }

    void load();
    return () => {
      active = false;
    };
  }, [userId]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return <ModuleDetailPage id={userId} config={resolvedConfig} />;
}
