import { WebhookForm } from "@/components/forms/webhook-form";
import { ResourceDetailLayout } from "@/components/details/resource-detail-layout";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <ResourceDetailLayout
      backHref="/webhooks"
      backLabel="Back to webhooks"
      title="Webhook endpoint"
      description={`Webhook ID: ${params.id}`}
      status="Active"
    >
      <WebhookForm />
    </ResourceDetailLayout>
  );
}
