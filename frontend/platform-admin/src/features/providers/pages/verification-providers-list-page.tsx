import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

export function VerificationProvidersListPage() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Verification providers"
        title="Verification Providers"
        description="Provider registry management is not yet connected to the platform-admin console."
      />
      <EmptyState
        title="Verification providers are hidden"
        description="This area is postponed until a platform-admin provider service is available."
      />
    </div>
  );
}
