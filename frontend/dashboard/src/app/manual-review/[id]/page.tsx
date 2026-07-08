import { ReviewWorkbench } from "@/features/review/components/review-workbench";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <ResourceDetailLayout
      backHref="/manual-review"
      backLabel="Back to manual review"
      title="Manual review case"
      description={`Case ID: ${params.id}`}
      status="Review required"
    >
      <ReviewWorkbench />
    </ResourceDetailLayout>
  );
}
