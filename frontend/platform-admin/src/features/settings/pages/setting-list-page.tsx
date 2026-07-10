import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { settingsConfig } from "@/features/settings/mock-data";

export function SettingsListPage() {
  return <AdminListPage config={createAdminListConfig(settingsConfig)} />;
}