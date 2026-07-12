import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type VerificationProviderDetailPageProps = {
  providerId: string;
};

export function VerificationProviderDetailPage({
  providerId,
}: VerificationProviderDetailPageProps) {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Verification providers"
        title={`Verification Provider ${providerId}`}
        description="Provider detail is not connected to the platform-admin console yet."
      />
      <EmptyState
        title="Verification provider detail is hidden"
        description="This route is intentionally postponed until a platform-admin provider API exists."
      />
    </div>
  );
}
