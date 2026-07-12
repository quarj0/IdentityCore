import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

type AuditDetailPageProps = {
  auditId: string;
};

export function AuditDetailPage({ auditId }: AuditDetailPageProps) {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform audit"
        title={`Audit ${auditId}`}
        description="Detailed audit inspection is not exposed in the platform-admin console yet."
      />
      <EmptyState
        title="Audit detail is not connected here"
        description="This route is intentionally kept out of the internal console until a platform-admin API is available."
      />
    </div>
  );
}
