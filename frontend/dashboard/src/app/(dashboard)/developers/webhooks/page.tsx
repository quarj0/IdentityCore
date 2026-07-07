import type { Metadata } from "next";
import { Plus, Edit2, Trash2, Webhook, CheckCircle2, XCircle } from "lucide-react";
import {
  Card,
  CardContent,
  Badge,
  Button,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Webhooks" };

const webhooks = [
  {
    id: "wh-001",
    url: "https://api.acmecorp.com/hooks/identity",
    events: ["verification.approved", "verification.rejected", "verification.review"],
    status: "active",
    lastDelivery: "2026-07-06 22:15",
    successRate: "99.2%",
  },
  {
    id: "wh-002",
    url: "https://hooks.acmecorp.com/compliance",
    events: ["verification.approved"],
    status: "active",
    lastDelivery: "2026-07-06 22:11",
    successRate: "100%",
  },
  {
    id: "wh-003",
    url: "https://old-system.acmecorp.com/notify",
    events: ["verification.approved", "verification.rejected"],
    status: "failing",
    lastDelivery: "2026-07-04 08:22",
    successRate: "12.5%",
  },
];

export default function WebhooksPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Webhooks</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Receive real-time event notifications for verification activity.
          </p>
        </div>
        <Button id="create-webhook" className="gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          Add Endpoint
        </Button>
      </div>

      <div className="space-y-3">
        {webhooks.map((wh) => (
          <Card key={wh.id} id={`webhook-card-${wh.id}`}>
            <CardContent className="p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    {wh.status === "active" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-destructive" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <code className="text-sm font-mono truncate max-w-xs">{wh.url}</code>
                      <Badge variant={wh.status === "active" ? "success" : "destructive"}>
                        {wh.status === "active" ? "Active" : "Failing"}
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {wh.events.map((e) => (
                        <Badge key={e} variant="outline" className="text-xs font-mono font-normal">
                          {e}
                        </Badge>
                      ))}
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Last delivery: {wh.lastDelivery}</span>
                      <span>Success rate: {wh.successRate}</span>
                    </div>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button variant="outline" size="sm" className="h-8 gap-1.5" id={`edit-webhook-${wh.id}`}>
                    <Edit2 className="h-3.5 w-3.5" />
                    Edit
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" id={`delete-webhook-${wh.id}`}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
