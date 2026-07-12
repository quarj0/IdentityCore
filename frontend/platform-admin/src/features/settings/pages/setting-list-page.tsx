import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

export function SettingsListPage() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform configuration"
        title="Settings"
        description="This area is reserved for future platform configuration APIs and is intentionally not faked."
      />

      <EmptyState
        title="Settings not wired yet"
        description="We are hiding fake configuration data until the backend exposes a real admin contract."
      />
    </div>
  );
}
