import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { settingsConfig } from "@/features/settings/mock-data";

export function SettingsListPage() {
  return <AdminListPage config={settingsConfig} />;
}