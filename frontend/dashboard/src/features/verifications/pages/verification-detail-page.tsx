import { DecisionCard } from "../components/decision-card";
import { EvidenceGallery } from "../components/evidence-gallery";
import { JsonViewer } from "@/components/dashboard-ui/json-viewer";
import { DetailCard } from "@/components/dashboard-ui/detail-card";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";
import { verificationEvidence } from "@/data/dashboard-details";

export function VerificationDetailPage({ id }: { id: string }) {
  return (
    <ResourceDetailLayout
      backHref="/verification-requests"
      backLabel="Back to requests"
      title="Verification request"
      description={`Verification ID: ${id}`}
      status="Approved"
    >
      <div className="grid gap-6 xl:grid-cols-[0.6fr_0.4fr]">
        <div className="space-y-6">
          <EvidenceGallery />
          <DetailCard title="Raw evidence payload">
            <JsonViewer value={verificationEvidence} />
          </DetailCard>
        </div>

        <DecisionCard />
      </div>
    </ResourceDetailLayout>
  );
}
