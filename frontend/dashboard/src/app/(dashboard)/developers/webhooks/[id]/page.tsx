import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";
import { webhooks } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Webhook Detail" };

export default async function WebhookDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const webhook = webhooks.find((item) => item.id === id);

  if (!webhook) notFound();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Webhook endpoint"
        description={webhook.url}
        actions={
          <>
            <Badge variant={webhook.status === "active" ? "success" : "destructive"}>
              {webhook.status === "active" ? "Active" : "Failing"}
            </Badge>
            <Button>Rotate secret</Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Delivery health</CardTitle>
            <CardDescription>Recent signal for this webhook endpoint.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Success rate</div>
                <div className="mt-1 font-semibold text-foreground">{webhook.successRate}</div>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Last delivery</div>
                <div className="mt-1 font-semibold text-foreground">{webhook.lastDelivery}</div>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Secret rotation</div>
                <div className="mt-1 font-semibold text-foreground">{webhook.secretRotation}</div>
              </div>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Subscribed events</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {webhook.events.map((event) => (
                  <Badge key={event} variant="outline">{event}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent delivery summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="rounded-lg border border-border p-4">2xx deliveries remain below retry threshold.</div>
            <div className="rounded-lg border border-border p-4">Payload signing enabled with HMAC secret.</div>
            <div className="rounded-lg border border-border p-4">No endpoint changes in the last 30 days.</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
