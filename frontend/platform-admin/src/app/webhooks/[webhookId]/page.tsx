import { WebhookDetailPage } from "@/features/webhooks/pages/webhook-detail-page";

type PageProps = {
  params: Promise<{
    webhookId: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { webhookId } = await params;
  return <WebhookDetailPage webhookId={webhookId} />;
}
