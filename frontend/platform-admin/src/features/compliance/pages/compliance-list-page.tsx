import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

export function ComplianceListPage() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Compliance"
        title="Compliance"
        description="Tenant compliance policies are not exposed in the platform-admin console yet."
      />
      <EmptyState
        title="Compliance is not connected here"
        description="This section stays hidden until there is a platform-admin compliance service."
      />
    </div>
  );
}
