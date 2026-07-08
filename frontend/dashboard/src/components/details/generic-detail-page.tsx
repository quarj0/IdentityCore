import { DetailCard } from "@/components/dashboard-ui/detail-card";
import { JsonViewer } from "@/components/dashboard-ui/json-viewer";
import { Timeline } from "@/components/dashboard-ui/timeline";
import { ResourceDetailLayout } from "./resource-detail-layout";
import { detailTimeline, verificationEvidence } from "@/data/dashboard-details";

interface GenericDetailPageProps {
  backHref: string;
  backLabel: string;
  title: string;
  description: string;
}

export function GenericDetailPage({
  backHref,
  backLabel,
  title,
  description,
}: GenericDetailPageProps) {
  return (
    <ResourceDetailLayout
      backHref={backHref}
      backLabel={backLabel}
      title={title}
      description={description}
      status="Sandbox"
    >
      <div className="grid gap-6 xl:grid-cols-[0.6fr_0.4fr]">
        <DetailCard title="Details">
          <JsonViewer value={verificationEvidence} />
        </DetailCard>

        <DetailCard title="Timeline">
          <Timeline items={detailTimeline} />
        </DetailCard>
      </div>
    </ResourceDetailLayout>
  );
}
