import type { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";

export const metadata: Metadata = { title: "Activity" };

const activities = [
  "Cross-tenant verification volume is up 11.8% over the last 30 days.",
  "Manual review queue pressure is concentrated in West Africa and new enterprise pilots.",
  "Webhook delivery retries remain isolated to three tenants with legacy receivers.",
];

export default function PlatformAdminActivityPage() {
  return (
    <AdminPageFrame title="Activity" description="Cross-tenant verification operations, queue movement, and regional trends.">
      <div className="space-y-4">
        {activities.map((activity) => (
          <Card key={activity}>
            <CardHeader><CardTitle className="text-base">Operational signal</CardTitle></CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">{activity}</CardContent>
          </Card>
        ))}
      </div>
    </AdminPageFrame>
  );
}
