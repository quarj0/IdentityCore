import { SettingDetailPage } from "@/features/settings/pages/setting-detail-page";

type PageProps = { params: { settingId: string } };

export default async function Page({ params }: PageProps) {
  const { settingId } = await params;
  return <SettingDetailPage settingId={settingId} />;
}
