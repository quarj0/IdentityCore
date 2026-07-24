"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminDetailPage as ModuleDetailPage } from "@/components/admin-module/admin-detail-page";
import {
  adminUserToAdminRecord,
  buildPlatformAdminConfig,
  fetchPlatformAdminRecord,
} from "@/features/users/live-data";
import { DisableAdminDialog } from "@/features/users/components/disable-admin-dialog";

type AdminDetailPageProps = {
  userId: string;
};

export function AdminDetailPage({ userId }: AdminDetailPageProps) {
  const [config, setConfig] =
    useState<ReturnType<typeof buildPlatformAdminConfig> | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);
  const [adminName, setAdminName] = useState("");
  const [adminStatus, setAdminStatus] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      const user = await fetchPlatformAdminRecord(userId);
      if (!active || !user) return;

      setConfig(buildPlatformAdminConfig([adminUserToAdminRecord(user)]));
      setAdminName([user.firstName, user.lastName].filter(Boolean).join(" ") || user.email);
      setAdminStatus(user.status);
    }

    void load();
    return () => {
      active = false;
    };
  }, [userId, refreshToken]);

  const resolvedConfig = useMemo(() => config, [config]);

  if (!resolvedConfig) {
    return null;
  }

  return (
    <div className="space-y-4">
      {adminStatus === "active" ? (
        <div className="flex justify-end">
          <DisableAdminDialog
            adminName={adminName}
            userId={userId}
            onDeactivated={() => setRefreshToken((value) => value + 1)}
          />
        </div>
      ) : null}
      <ModuleDetailPage id={userId} config={resolvedConfig} />
    </div>
  );
}
