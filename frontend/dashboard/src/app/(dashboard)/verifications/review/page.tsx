import type { Metadata } from "next";
import { CheckCircle2, XCircle, User, Eye, FileText } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Button,
  Avatar,
  AvatarFallback,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Manual Review" };

const queue = [
  {
    id: "rev-041",
    subject: "Amara Diallo",
    email: "amara.d@sample.io",
    policy: "Enhanced KYC",
    reason: "Face match confidence below threshold (68%)",
    flaggedAt: "2026-07-06 21:47",
    priority: "high",
  },
  {
    id: "rev-040",
    subject: "Tomás Ferreira",
    email: "tomas.f@br.org",
    policy: "Standard KYC",
    reason: "Document authenticity score low (72%)",
    flaggedAt: "2026-07-06 19:12",
    priority: "medium",
  },
  {
    id: "rev-039",
    subject: "Yuki Tanaka",
    email: "y.tanaka@jp.co",
    policy: "Enhanced KYC",
    reason: "Liveness check inconclusive",
    flaggedAt: "2026-07-05 16:30",
    priority: "medium",
  },
  {
    id: "rev-038",
    subject: "Olumide Adeyemi",
    email: "o.adeyemi@ng.net",
    policy: "Standard KYC",
    reason: "Multiple submission attempts detected",
    flaggedAt: "2026-07-05 14:09",
    priority: "low",
  },
];

const PRIORITY_CONFIG = {
  high: { label: "High", variant: "destructive" as const },
  medium: { label: "Medium", variant: "warning" as const },
  low: { label: "Low", variant: "secondary" as const },
};

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function ManualReviewPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Manual Review</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {queue.length} cases requiring your attention.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {queue.map((item) => {
          const pCfg = PRIORITY_CONFIG[item.priority as keyof typeof PRIORITY_CONFIG];
          return (
            <Card key={item.id} id={`review-card-${item.id}`} className="transition-shadow hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-4">
                    <Avatar className="h-9 w-9 shrink-0 mt-0.5">
                      <AvatarFallback className="text-xs">{initials(item.subject)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">{item.subject}</span>
                        <Badge variant={pCfg.variant} className="text-xs">
                          {pCfg.label} Priority
                        </Badge>
                        <span className="font-mono text-xs text-muted-foreground">{item.id}</span>
                      </div>
                      <div className="mt-0.5 text-sm text-muted-foreground">{item.email} · {item.policy}</div>
                      <div className="mt-2 flex items-start gap-1.5 rounded-md bg-muted/60 px-3 py-2">
                        <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">{item.reason}</span>
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">Flagged {item.flaggedAt}</div>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2 sm:flex-col sm:items-end">
                    <Button size="sm" variant="outline" id={`review-view-${item.id}`} className="gap-1.5 h-8">
                      <Eye className="h-3.5 w-3.5" />
                      Review
                    </Button>
                    <div className="flex gap-2">
                      <Button size="sm" id={`approve-${item.id}`} className="gap-1.5 h-8 bg-emerald-600 hover:bg-emerald-700 text-white">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Approve
                      </Button>
                      <Button size="sm" variant="destructive" id={`reject-${item.id}`} className="gap-1.5 h-8">
                        <XCircle className="h-3.5 w-3.5" />
                        Reject
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
