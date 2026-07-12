import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";

export function AiProvidersListPage() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="AI infrastructure"
        title="AI Providers"
        description="This section is not yet connected to a backend admin API. The live console currently uses the Verification Providers area instead."
      />

      <EmptyState
        title="AI Providers not wired yet"
        description="We are keeping this section honest until there is a real backend API and governance model for it."
      />
    </div>
  );
}
