import { JsonViewer } from "@/components/dashboard-ui/json-viewer";
import { DetailCard } from "@/components/dashboard-ui/detail-card";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";
import { verificationEvidence } from "@/data/dashboard-details";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <ResourceDetailLayout
      backHref="/audit-logs"
      backLabel="Back to audit logs"
      title="Audit event"
      description={`Event ID: ${params.id}`}
      status="Complete"
    >
      <DetailCard title="Event payload">
        <JsonViewer value={verificationEvidence} />
      </DetailCard>
    </ResourceDetailLayout>
  );
}
