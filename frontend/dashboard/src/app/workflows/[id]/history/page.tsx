import { DetailCard } from "@/components/dashboard-ui/detail-card";
import { Timeline } from "@/components/dashboard-ui/timeline";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";
import { detailTimeline } from "@/data/dashboard-details";

export default function Page() {
  return (
    <ResourceDetailLayout
      backHref="/workflows/demo"
      backLabel="Back to workflow"
      title="Workflow history"
      description="View workflow edits, versions, publishing events, and configuration changes."
      status="History"
    >
      <DetailCard title="Version timeline">
        <Timeline items={detailTimeline} />
      </DetailCard>
    </ResourceDetailLayout>
  );
}
