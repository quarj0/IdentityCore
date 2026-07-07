import type { Metadata } from "next";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";
import { tenants } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Onboarding" };

export default function PlatformAdminOnboardingPage() {
  return (
    <AdminPageFrame
      title="Onboarding queue"
      description="Review pending organization onboarding, supporting documents, and production access readiness."
      actions={<Button>Open review runbook</Button>}
    >
      <div className="space-y-4">
        {tenants.map((tenant) => (
          <Card key={tenant.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-base">{tenant.name}</CardTitle>
                <Badge variant={tenant.status === "Pending approval" ? "warning" : "outline"}>{tenant.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>{tenant.tier} tier · {tenant.region}</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">Review documents</Button>
                <Button size="sm">Approve</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </AdminPageFrame>
  );
}
