"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage as ModuleDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  buildSettingsConfig,
  fetchSettingRecord,
  settingToAdminRecord,
} from "@/features/settings/live-data";

type SettingDetailPageProps = {
  settingId: string;
};

export function SettingDetailPage({ settingId }: SettingDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildSettingsConfig> | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const setting = await fetchSettingRecord(settingId);
      if (!active || !setting) return;

      setConfig(buildSettingsConfig([settingToAdminRecord(setting)]));
    }

    void load();
    return () => {
      active = false;
    };
  }, [settingId]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return <ModuleDetailPage id={settingId} config={resolvedConfig} />;
}
