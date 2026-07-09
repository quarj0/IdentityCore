import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { settingsConfig } from "@/features/settings/mock-data";

type SettingDetailPageProps = {
  settingId: string;
};

export function SettingDetailPage({ settingId }: SettingDetailPageProps) {
  return <AdminDetailPage id={settingId} config={settingsConfig} />;
}