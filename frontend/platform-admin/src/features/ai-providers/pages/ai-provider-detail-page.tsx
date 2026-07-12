import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type AiProviderDetailPageProps = {
  providerId: string;
};

export function AiProviderDetailPage({ providerId }: AiProviderDetailPageProps) {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="AI infrastructure"
        title="AI Provider detail"
        description={`Provider ${providerId} is not yet backed by a production admin API.`}
      />

      <EmptyState
        title="AI Provider not wired yet"
        description="Until the backend model and admin API exist, this screen stays as an explicit placeholder."
      />
    </div>
  );
}
