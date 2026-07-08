import { DetailCard } from "@/components/dashboard-ui/detail-card";
import { Timeline } from "@/components/dashboard-ui/timeline";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";
import { detailTimeline } from "@/data/dashboard-details";

export default function Page() {
  return (
    <ResourceDetailLayout
      backHref="/templates/demo"
      backLabel="Back to template"
      title="Template versions"
      description="Review previous template versions and publishing history."
      status="Versions"
    >
      <DetailCard title="Version history">
        <Timeline items={detailTimeline} />
      </DetailCard>
    </ResourceDetailLayout>
  );
}