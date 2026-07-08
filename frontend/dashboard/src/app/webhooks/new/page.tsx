import { WebhookForm } from "@/components/forms/webhook-form";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Add webhook"
        description="Create a webhook endpoint for workflow and verification events."
      />
      <WebhookForm />
    </div>
  );
}
