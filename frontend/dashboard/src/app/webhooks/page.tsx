import { Webhook } from "lucide-react";
import { ResourcePage } from "@/components/shared/resource-page";
import { tableData } from "@/data/mock-tables";

export default function WebhooksPage() {
  return (
    <ResourcePage
      title="Webhooks"
      description="Send workflow and verification events to your application."
      actionLabel="Add webhook"
      emptyTitle="No webhook endpoints"
      emptyDescription="Add an endpoint to receive workflow events."
      icon={Webhook}
      {...tableData.webhooks}
    />
  );
}
