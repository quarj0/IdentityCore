import { SettingDetailPage } from "@/features/settings/pages/setting-detail-page";

type PageProps = { params: { settingId: string } };

export default function Page({ params }: PageProps) {
  return <SettingDetailPage settingId={params.settingId} />;
}