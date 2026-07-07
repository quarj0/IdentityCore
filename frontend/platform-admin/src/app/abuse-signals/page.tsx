import type { Metadata } from "next";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";
import { abuseSignals } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Abuse Signals" };

export default function PlatformAdminAbuseSignalsPage() {
  return (
    <AdminPageFrame title="Abuse signals" description="Review suspicious patterns that may require intervention or tenant action.">
      <div className="space-y-4">
        {abuseSignals.map((signal) => (
          <Card key={signal.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-base">{signal.signal}</CardTitle>
                <Badge variant={signal.severity === "High" ? "destructive" : "warning"}>{signal.severity}</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>{signal.tenant}</span>
              <span>{signal.state}</span>
            </CardContent>
          </Card>
        ))}
      </div>
    </AdminPageFrame>
  );
}
