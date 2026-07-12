import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type ComplianceDetailPageProps = {
  policyId: string;
};

export function ComplianceDetailPage({ policyId }: ComplianceDetailPageProps) {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Compliance"
        title={`Compliance ${policyId}`}
        description="Detailed compliance policy controls are not exposed in the platform-admin console yet."
      />
      <EmptyState
        title="Compliance detail is not connected here"
        description="This route is intentionally kept out of the internal console until a platform-admin compliance API exists."
      />
    </div>
  );
}
