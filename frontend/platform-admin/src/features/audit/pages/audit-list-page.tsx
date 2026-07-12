import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

export function AuditListPage() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform audit"
        title="Audit"
        description="Tenant-scoped audit data is not exposed in the platform-admin console yet."
      />
      <EmptyState
        title="Audit is not connected here"
        description="This surface will stay hidden from the internal console until a platform-admin API is available."
      />
    </div>
  );
}
