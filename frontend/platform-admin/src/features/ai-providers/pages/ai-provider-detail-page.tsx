"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage as ModuleDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  buildAiProviderConfig,
  fetchAiProviderRecord,
  providerToAdminRecord,
} from "@/features/ai-providers/live-data";

type AiProviderDetailPageProps = {
  providerId: string;
};

export function AiProviderDetailPage({ providerId }: AiProviderDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildAiProviderConfig> | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      const data = await fetchAiProviderRecord(providerId);
      if (!active || !data.provider) return;

      setConfig(
        buildAiProviderConfig(
          [providerToAdminRecord(data.provider)],
          data.checks,
        ),
      );
    }

    void load();
    return () => {
      active = false;
    };
  }, [providerId]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return <ModuleDetailPage id={providerId} config={resolvedConfig} />;
}
