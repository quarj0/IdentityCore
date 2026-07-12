import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type SettingDetailPageProps = {
  settingId: string;
};

export function SettingDetailPage({ settingId }: SettingDetailPageProps) {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform configuration"
        title="Setting detail"
        description={`Setting ${settingId} does not have a live backend API yet.`}
      />

      <EmptyState
        title="Settings detail not wired yet"
        description="This page is intentionally a placeholder until the backend configuration API is available."
      />
    </div>
  );
}
